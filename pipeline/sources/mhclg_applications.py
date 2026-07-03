"""MHCLG planning application statistics: PS1/PS2 district-matters open data CSVs.

PS1: applications received / decided / withdrawn per LPA per quarter (1996→).
PS2: decisions, granted, refused, and speed of decision per development type
(1979→), with each group split into decisions "excluding PAs" (no performance
agreement: PPA / extension of time / EIA) and "PAs only". That split is what
lets us measure how much extension-of-time agreements flatter headline speed.

County matters (CPS1/CPS2, minerals & waste) are intentionally not loaded —
volumes are tiny and they would double-count against district totals.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from ..authority_lookup import is_gss
from ..common import SourceError, log, sources_config
from ..common import download as fetch
from ..quarters import parse_quarter

NA_VALUES = ["..", "-", "", "x", "z", ":"]

# PS2 development-type groups -> our dev_type keys.
GROUPS = {
    "grand total": "all",
    "major total": "major",
    "minor total": "minor",
    "(other) total": "other",
    "major dwellings": "major_res",
    "minor dwellings": "minor_res",
    "(other) householder developments": "householder",
}
# Groups that publish explicit in-time counts (the headline speed measure).
TOTAL_GROUPS = {"grand total", "major total", "minor total", "(other) total"}
# Detail groups publish speed *bands* instead; statutory deadline weeks per group.
BAND_EDGES = ["8 weeks", "8 to 13 weeks", "13 to 16 weeks", "16 to 26 weeks", "26 to 52 weeks"]
STATUTORY_BANDS = {"major dwellings": 2, "minor dwellings": 1, "(other) householder developments": 1}
# how many leading bands count as within statutory time (13 wks major, 8 wks minor/householder)


def _find_header(path: Path, sentinel: str = "Region,LPANM,LPACD,Quarter") -> int:
    """Government CSVs open with a variable number of title/footnote rows."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if line.startswith(sentinel):
                return i
            if i > 30:
                break
    raise SourceError(f"{path.name}: header row starting '{sentinel}' not found in first 30 lines")


def _read(path: Path, usecols=None) -> pd.DataFrame:
    header = _find_header(path)
    try:
        df = pd.read_csv(
            path, skiprows=header, na_values=NA_VALUES, keep_default_na=True,
            usecols=usecols, dtype={"LPACD": str, "LPANM": str, "Region": str, "Quarter": str},
            encoding="utf-8", encoding_errors="replace", low_memory=False,
        )
    except ValueError as e:
        raise SourceError(f"{path.name}: {e}") from e
    df = df[df["LPANM"].notna() & df["LPACD"].notna()]
    # Drop partial-area rows for authorities that overlap a National Park.
    df = df[~df["LPANM"].str.contains("within National Park", case=False, na=False)]
    df["quarter"] = df["Quarter"].map(parse_quarter)
    return df


def parse_ps1(path: Path) -> pd.DataFrame:
    """Long facts from PS1: received / decided_all_types / withdrawn per LPA-quarter."""
    cols = {
        "Applications received": "received",
        "Applications decided": "decided_all_types",
        "Applications withdrawn": "withdrawn",
    }
    df = _read(path, usecols=lambda c: c in ("Region", "LPANM", "LPACD", "Quarter") or c in cols)
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SourceError(f"{path.name}: expected PS1 columns missing: {missing}")
    long = df.melt(
        id_vars=["LPACD", "LPANM", "Region", "quarter"],
        value_vars=list(cols), var_name="col", value_name="value",
    ).dropna(subset=["value"])
    long["metric"] = long["col"].map(cols)
    long["dev_type"] = "all"
    return long[["LPACD", "LPANM", "Region", "quarter", "dev_type", "metric", "value"]]


def _ps2_wanted_columns() -> dict[str, tuple[str, str]]:
    """column name -> (dev_type, metric)."""
    want: dict[str, tuple[str, str]] = {}
    for group, dt in GROUPS.items():
        want[f"Total decisions; {group} (all)"] = (dt, "decisions")
        want[f"Total granted; {group} (all)"] = (dt, "granted")
        want[f"Total refused; {group} (all)"] = (dt, "refused")
        want[f"Total decisions; {group} (PAs only)"] = (dt, "decisions_pa")
        want[f"Total decisions in time; {group} (PAs only)"] = (dt, "intime_pa")
        if group in TOTAL_GROUPS:
            want[f"Total decisions; {group} (excluding PAs)"] = (dt, "decisions_expa")
            want[f"Total decisions in time; {group} (excluding PAs)"] = (dt, "intime_expa")
        else:
            for i, band in enumerate(BAND_EDGES, start=1):
                want[f"Total decided within {band}; {group} (excluding PAs)"] = (dt, f"band{i}")
            want[f"Total decided beyond 52 weeks; {group} (excluding PAs)"] = (dt, "band6")
    return want


def parse_ps2(path: Path) -> pd.DataFrame:
    """Long facts from PS2 for the dev-type groups we track."""
    want = _ps2_wanted_columns()
    df = _read(path, usecols=lambda c: c in ("Region", "LPANM", "LPACD", "Quarter") or c in want)
    missing = [c for c in want if c not in df.columns]
    if missing:
        raise SourceError(
            f"{path.name}: {len(missing)} expected PS2 columns missing, e.g. {missing[:3]} — "
            "MHCLG may have renamed columns; compare against _ps2_wanted_columns()."
        )
    value_cols = [c for c in df.columns if c in want]
    long = df.melt(
        id_vars=["LPACD", "LPANM", "Region", "quarter"],
        value_vars=value_cols, var_name="col", value_name="value",
    ).dropna(subset=["value"])
    long[["dev_type", "metric"]] = pd.DataFrame(
        long["col"].map(want).tolist(), index=long.index
    )
    return long[["LPACD", "LPANM", "Region", "quarter", "dev_type", "metric", "value"]]


AUTH_TYPE_BY_PREFIX = {
    "E06": "unitary", "E07": "district", "E08": "metropolitan", "E09": "london_borough",
    "E26": "national_park", "E51": "development_corporation", "E61": "development_corporation",
}


def authority_type(code: str) -> str:
    if not is_gss(code):
        return "legacy"
    return AUTH_TYPE_BY_PREFIX.get(code[:3], "other")


def upsert_authorities(conn: sqlite3.Connection, frames: list[pd.DataFrame]) -> None:
    seen = (
        pd.concat(f[["LPACD", "LPANM", "Region", "quarter"]] for f in frames)
        .sort_values("quarter")
        .groupby("LPACD")
        .last()  # most recent name/region wins
        .reset_index()
    )
    from ..authority_lookup import canonical

    for _, r in seen.iterrows():
        code, name, region = r["LPACD"].strip(), r["LPANM"].strip(), (r["Region"] or "").strip()
        canon_code, _ = canonical(code, name)
        active = 1 if (canon_code == code and is_gss(code)) else 0
        successor = canon_code if canon_code != code else None
        conn.execute(
            """INSERT INTO authorities (code, name, region, authority_type, active, successor_code)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(code) DO UPDATE SET
                 name=excluded.name,
                 region=COALESCE(NULLIF(excluded.region,''), authorities.region),
                 authority_type=excluded.authority_type,
                 active=excluded.active,
                 successor_code=excluded.successor_code""",
            (code, name, region or None, authority_type(code), active, successor),
        )


def load_facts(conn: sqlite3.Connection, long: pd.DataFrame, source: str) -> int:
    conn.execute("DELETE FROM facts WHERE source = ?", (source,))
    rows = (
        (r.LPACD.strip(), r.quarter, r.dev_type, r.metric, float(r.value), source)
        for r in long.itertuples(index=False)
    )
    cur = conn.executemany(
        "INSERT OR REPLACE INTO facts (authority_code, quarter, dev_type, metric, value, source) VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    return cur.rowcount


def run(conn: sqlite3.Connection, offline: bool = False) -> int:
    cfg = sources_config()["mhclg_applications"]["files"]
    ps1_path = fetch(cfg["ps1"]["url"], cfg["ps1"]["filename"], offline=offline)
    ps2_path = fetch(cfg["ps2"]["url"], cfg["ps2"]["filename"], offline=offline)

    log.info("parsing %s", ps1_path.name)
    ps1 = parse_ps1(ps1_path)
    log.info("PS1: %d fact rows", len(ps1))
    log.info("parsing %s (large file, ~30s)", ps2_path.name)
    ps2 = parse_ps2(ps2_path)
    log.info("PS2: %d fact rows", len(ps2))
    if len(ps1) < 10_000 or len(ps2) < 100_000:
        raise SourceError(
            f"Suspiciously few rows parsed (PS1={len(ps1)}, PS2={len(ps2)}) — "
            f"check {ps1_path.name} / {ps2_path.name} layout."
        )

    upsert_authorities(conn, [ps1, ps2])
    n = load_facts(conn, ps1, "ps1") + load_facts(conn, ps2, "ps2")
    return n
