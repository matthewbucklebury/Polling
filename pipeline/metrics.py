"""Derive analytical metrics from loaded facts.

Everything here works on *canonical* authorities: predecessor districts are
mapped to their successors (counts are additive) so series stay continuous
across local government reorganisation. Ratios are computed from summed counts
in both windows — the 4Q (rolling annual) ratio is sum(num)/sum(den) over the
trailing four quarters, never a mean of ratios.

Output: the `metrics` table, including England ('ENG') and region ('REG:<name>')
aggregates, and the friction score with its component percentiles.
"""
from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd

from .common import log, settings

# (metric name, dev_type, numerator expression, denominator expression) for ratios;
# expressions are column names of the wide count frame.
COUNT_METRICS = {  # stored as plain sums, per dev_type
    "decisions": ("decisions", ["all", "major", "minor", "other", "major_res", "minor_res", "householder"]),
    "granted": ("granted", ["all", "major_res"]),
    "refused": ("refused", ["all", "major_res"]),
    "received": ("received", ["all"]),
    "withdrawn": ("withdrawn", ["all"]),
    "appeals_decided": ("appeals_decided", ["all", "major_res"]),
    "appeals_allowed": ("appeals_allowed", ["all", "major_res"]),
}
APPROVAL_DEV_TYPES = ["all", "major", "minor", "other", "major_res", "minor_res", "householder"]
SPEED_TOTAL_DEV_TYPES = ["all", "major", "minor"]  # groups with explicit in-time columns
BANDS = [f"band{i}" for i in range(1, 7)]
STATUTORY_BAND_COUNT = {"major_res": 2, "minor_res": 1, "householder": 1}  # 13 wks major, 8 wks minor


def _load_canonical_facts(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    """facts -> (wide counts frame indexed by [code, dev_type, quarter], authorities df).

    Predecessors are summed into successors; region/England aggregates appended
    as pseudo-codes REG:<name> / ENG.
    """
    auth = pd.read_sql("SELECT code, name, region, authority_type, active, successor_code FROM authorities", conn)
    succ = {
        r.code: (r.successor_code if isinstance(r.successor_code, str) and r.successor_code else r.code)
        for r in auth.itertuples(index=False)
    }
    region_of = {r.code: r.region for r in auth.itertuples(index=False) if r.active == 1}

    facts = pd.read_sql("SELECT authority_code, quarter, dev_type, metric, value FROM facts", conn)
    if facts.empty:
        return pd.DataFrame(), auth
    facts["code"] = facts["authority_code"].map(lambda c: succ.get(c, c))
    grouped = facts.groupby(["code", "dev_type", "quarter", "metric"], sort=False)["value"].sum()

    # England and region aggregates over English principal authorities.
    lpa_mask = facts["code"].str.match(r"^E0[6789]")
    eng = facts[lpa_mask].groupby(["dev_type", "quarter", "metric"], sort=False)["value"].sum().reset_index()
    eng["code"] = "ENG"
    reg = facts[lpa_mask].copy()
    reg["region"] = reg["code"].map(region_of)
    reg = reg.dropna(subset=["region"])
    reg = reg.groupby(["region", "dev_type", "quarter", "metric"], sort=False)["value"].sum().reset_index()
    reg["code"] = "REG:" + reg["region"]

    all_rows = pd.concat(
        [grouped.reset_index(), eng[["code", "dev_type", "quarter", "metric", "value"]],
         reg[["code", "dev_type", "quarter", "metric", "value"]]],
        ignore_index=True,
    )
    wide = all_rows.pivot_table(index=["code", "dev_type", "quarter"], columns="metric", values="value", aggfunc="sum")
    wide = wide.sort_index()
    return wide, auth


def _rolling(wide: pd.DataFrame) -> pd.DataFrame:
    """Trailing-4-quarter sums of every count column, grouped by (code, dev_type)."""
    return (
        wide.groupby(level=["code", "dev_type"], sort=False)
        .rolling(4, min_periods=4)
        .sum()
        .droplevel([0, 1])  # rolling duplicates the group levels
    )


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    return (num / den.where(den > 0)).astype(float)


def _derive_frame(wide: pd.DataFrame) -> pd.DataFrame:
    """Wide counts (one window) -> long metric rows (code, quarter, metric, value)."""
    out: list[pd.DataFrame] = []

    def emit(sub: pd.Series, metric: str) -> None:
        s = sub.dropna()
        if s.empty:
            return
        df = s.rename("value").reset_index()[["code", "quarter", "value"]]
        df["metric"] = metric
        out.append(df)

    def dev(dt: str) -> pd.DataFrame:
        try:
            return wide.xs(dt, level="dev_type")
        except KeyError:
            return pd.DataFrame()

    for dt in APPROVAL_DEV_TYPES:
        d = dev(dt)
        if d.empty or "decisions" not in d:
            continue
        if "granted" in d:
            emit(_safe_div(d["granted"], d["decisions"]) * 100, f"approval_rate_{dt}")
        emit(d["decisions"], f"decisions_{dt}")

    d = dev("all")
    if not d.empty:
        for c, m in [("received", "received_all"), ("withdrawn", "withdrawn_all"),
                     ("granted", "granted_all"), ("refused", "refused_all")]:
            if c in d:
                emit(d[c], m)

    for dt in SPEED_TOTAL_DEV_TYPES:
        d = dev(dt)
        if d.empty or "decisions_expa" not in d:
            continue
        den_all = d["decisions_expa"] + d["decisions_pa"]
        headline = _safe_div(d["intime_expa"] + d["intime_pa"], den_all) * 100
        statutory = _safe_div(d["intime_expa"], d["decisions_expa"]) * 100
        emit(headline, f"pct_intime_headline_{dt}")
        emit(statutory, f"pct_intime_statutory_{dt}")
        emit(_safe_div(d["decisions_pa"], den_all) * 100, f"eot_share_{dt}")
        emit(headline - statutory, f"eot_gap_{dt}")

    for dt, n_bands in STATUTORY_BAND_COUNT.items():
        d = dev(dt)
        if d.empty or "band1" not in d:
            continue
        bands = [b for b in BANDS if b in d]
        total_expa = d[bands].sum(axis=1, min_count=len(bands))
        within = d[[f"band{i}" for i in range(1, n_bands + 1)]].sum(axis=1, min_count=n_bands)
        emit(_safe_div(within, total_expa) * 100, f"pct_intime_statutory_{dt}")
        if "decisions_pa" in d:
            emit(_safe_div(d["decisions_pa"], total_expa + d["decisions_pa"]) * 100, f"eot_share_{dt}")

    # Appeals (dev_type 'all' and 'major_res' facts loaded by the PINS source)
    for dt, suffix in [("all", ""), ("major_res", "_major_res")]:
        d = dev(dt)
        if d.empty or "appeals_decided" not in d:
            continue
        emit(d["appeals_decided"], f"appeals_decided{suffix}")
        emit(_safe_div(d["appeals_allowed"], d["appeals_decided"]) * 100, f"overturn_rate{suffix}")
    d = dev("all")
    if not d.empty and "appeals_refusal_decided" in d:
        emit(_safe_div(d["appeals_refusal_allowed"], d["appeals_refusal_decided"]) * 100, "refusal_overturn_rate")
        if "refused" in d:
            emit(_safe_div(d["appeals_refusal_decided"], d["refused"]) * 100, "appeal_rate_refusals")

    if not out:
        return pd.DataFrame(columns=["code", "quarter", "metric", "value"])
    return pd.concat(out, ignore_index=True)


def _volume_trend(long_4q: pd.DataFrame) -> pd.DataFrame:
    """4Q decisions vs the authority's own previous-5-years average (per cent, 100 = on trend)."""
    d = long_4q[long_4q["metric"] == "decisions_all"].copy()
    if d.empty:
        return d
    d = d.sort_values(["code", "quarter"])
    base = (
        d.groupby("code")["value"]
        .apply(lambda s: s.shift(1).rolling(20, min_periods=12).mean())
        .reset_index(level=0, drop=True)
    )
    d["value"] = 100 * d["value"] / base.where(base > 0)
    d["metric"] = "decisions_vs_5yr"
    return d.dropna(subset=["value"])


def _friction(long_4q: pd.DataFrame, auth: pd.DataFrame) -> pd.DataFrame:
    """Composite friction score: weighted mean of percentile ranks across active
    authorities per quarter. Components + weights from settings.yml; each
    component percentile is stored alongside the composite."""
    cfg = settings()["friction_score"]["components"]
    active = set(auth[auth["active"] == 1]["code"])

    piv = long_4q.pivot_table(index=["code", "quarter"], columns="metric", values="value")
    piv = piv[piv.index.get_level_values("code").isin(active)]

    denominators = {
        "approval_rate_major_res": "decisions_major_res",
        "pct_intime_statutory_major": "decisions_major",
        "overturn_rate": "appeals_decided",
    }
    parts, weights = {}, {}
    for metric, c in cfg.items():
        if metric not in piv.columns:
            continue
        v = piv[metric].copy()
        den_col = denominators.get(metric)
        if den_col and den_col in piv.columns:
            v = v.where(piv[den_col] >= c.get("min_denominator", 0))
        pct = v.groupby(level="quarter").rank(pct=True) * 100
        if c["direction"] == "inverse":
            pct = 100 - pct
        parts[f"friction_{metric}"] = pct
        weights[f"friction_{metric}"] = float(c["weight"])

    if not parts:
        return pd.DataFrame(columns=["code", "quarter", "metric", "value"])
    comp = pd.DataFrame(parts)
    w = pd.Series(weights)
    mask = comp.notna()
    weight_sum = mask.mul(w, axis=1).sum(axis=1)
    comp["friction_score"] = comp.fillna(0).mul(w, axis=1).sum(axis=1) / weight_sum.where(weight_sum > 0)
    long = comp.reset_index().melt(id_vars=["code", "quarter"], var_name="metric", value_name="value")
    return long.dropna(subset=["value"])


def derive_all(conn: sqlite3.Connection) -> int:
    wide, auth = _load_canonical_facts(conn)
    if wide.empty:
        log.warning("no facts loaded; skipping metric derivation")
        return 0

    log.info("deriving quarterly metrics (%d count rows)", len(wide))
    q_long = _derive_frame(wide)
    q_long["window"] = "Q"

    log.info("deriving rolling-annual metrics")
    wide4 = _rolling(wide)
    q4_long = _derive_frame(wide4)
    q4_long["window"] = "4Q"

    extra = _volume_trend(q4_long[q4_long["window"] == "4Q"])
    fr = _friction(q4_long, auth)
    for e in (extra, fr):
        if not e.empty:
            e["window"] = "4Q"
    all_long = pd.concat([q_long, q4_long, extra, fr], ignore_index=True)
    # concat with empty frames leaves an object-dtype value column
    all_long["value"] = pd.to_numeric(all_long["value"], errors="coerce")
    all_long = all_long.dropna(subset=["value"])
    all_long = all_long[np.isfinite(all_long["value"])]

    log.info("writing %d metric rows", len(all_long))
    conn.execute("DELETE FROM metrics")
    conn.executemany(
        "INSERT OR REPLACE INTO metrics (authority_code, quarter, metric, window, value) VALUES (?,?,?,?,?)",
        ((r.code, r.quarter, r.metric, r.window, round(float(r.value), 4))
         for r in all_long.itertuples(index=False)),
    )
    conn.commit()
    return len(all_long)
