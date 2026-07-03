"""Planning Inspectorate (PINS) appeals: case-level casework database.

Two workbooks (current system + legacy "older casework") share the columns we
need: ONS LPA Code, LPA Name, Decision Date, Decision, Type of Casework,
Development Type, Reason for the Appeal. We count appeals with a substantive
decision (Allowed / Dismissed / Split) into quarterly facts per authority:

    appeals_decided / appeals_allowed / appeals_dismissed / appeals_split
    (dev_type 'all', and 'major_res' for Major dwellings appeals)
    appeals_refusal_decided / appeals_refusal_allowed
    (appeals against refusals only — the overturn-of-refusals measure)

Casework types kept: planning-style appeals a refused applicant could lodge
(s78 planning, householder, minor commercial). Enforcement, listed building,
advertisement etc. are excluded from the headline but easy to add.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from ..authority_lookup import is_gss
from ..common import SourceError, log, sources_config
from ..common import download as fetch
from ..quarters import quarter_of_date

CASEWORK_TYPES = {"Planning Appeal", "Householder (HAS)", "Commercial Appeal Service (CAS)"}
DECIDED = {"allowed", "dismissed", "split decision", "allowed with conditions"}
COLUMNS = ["Type of Casework", "LPA Name", "ONS LPA Code", "Decision Date", "Decision",
           "Development Type", "Reason for the Appeal"]


def parse_casework(path: Path, sheet: str) -> pd.DataFrame:
    """Case-level rows -> tidy appeals frame (code, name, quarter, outcome, dev, reason)."""
    try:
        df = pd.read_excel(path, sheet_name=sheet, usecols=lambda c: c in COLUMNS)
    except ValueError as e:
        raise SourceError(f"{path.name} sheet '{sheet}': {e}") from e
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise SourceError(f"{path.name} sheet '{sheet}': missing columns {missing}")

    df = df[df["Type of Casework"].isin(CASEWORK_TYPES)]
    df["decision"] = df["Decision"].astype(str).str.strip().str.lower()
    df = df[df["decision"].isin(DECIDED)]
    df["Decision Date"] = pd.to_datetime(df["Decision Date"], errors="coerce")
    df = df[df["Decision Date"].notna()]
    if df.empty:
        raise SourceError(f"{path.name} sheet '{sheet}': no decided appeals parsed — layout change?")

    out = pd.DataFrame({
        "code": df["ONS LPA Code"].astype(str).str.strip(),
        "name": df["LPA Name"].astype(str).str.strip(),
        "quarter": [quarter_of_date(d.year, d.month) for d in df["Decision Date"]],
        "outcome": df["decision"].map(
            lambda d: "allowed" if d in ("allowed", "allowed with conditions")
            else ("dismissed" if d == "dismissed" else "split")
        ),
        "is_major_res": df["Development Type"].astype(str).str.strip().str.lower() == "major dwellings",
        # 'Refusal', 'refused', 'Refusal - Reserved Matters', ... all count as refusal appeals
        "is_refusal": df["Reason for the Appeal"].astype(str).str.strip().str.lower().str.startswith("refus"),
    })
    return out


def aggregate(appeals: pd.DataFrame) -> pd.DataFrame:
    """Tidy appeals -> long facts (code, name, quarter, dev_type, metric, value)."""
    frames = []

    def counts(sub: pd.DataFrame, dev_type: str, prefix: str) -> pd.DataFrame:
        f = (
            sub.groupby(["code", "name", "quarter", "outcome"]).size()
            .unstack("outcome", fill_value=0)
            .reindex(columns=["allowed", "dismissed", "split"], fill_value=0)
        )
        f[f"{prefix}_decided"] = f.sum(axis=1)
        f = f.rename(columns={oc: f"{prefix}_{oc}" for oc in ("allowed", "dismissed", "split")})
        f = f.reset_index().melt(
            id_vars=["code", "name", "quarter"], var_name="metric", value_name="value"
        )
        f["dev_type"] = dev_type
        return f

    frames.append(counts(appeals, "all", "appeals"))
    frames.append(counts(appeals[appeals["is_major_res"]], "major_res", "appeals"))
    refusals = appeals[appeals["is_refusal"]]
    f = counts(refusals, "all", "appeals_refusal")
    frames.append(f[f["metric"].isin(["appeals_refusal_decided", "appeals_refusal_allowed"])])
    return pd.concat(frames, ignore_index=True)


def load(conn: sqlite3.Connection, facts: pd.DataFrame) -> int:
    conn.execute("DELETE FROM facts WHERE source = 'pins'")
    # Register any LPA not yet in authorities (e.g. county councils on minerals appeals).
    known = {r[0] for r in conn.execute("SELECT code FROM authorities")}
    from ..authority_lookup import canonical

    for code, name in facts[["code", "name"]].drop_duplicates().itertuples(index=False):
        if code in known:
            continue
        canon, _ = canonical(code, name)
        conn.execute(
            "INSERT OR IGNORE INTO authorities (code, name, authority_type, active, successor_code) VALUES (?,?,?,?,?)",
            (code, name, "legacy" if not is_gss(code) else "other",
             1 if (canon == code and is_gss(code)) else 0, canon if canon != code else None),
        )
        known.add(code)
    cur = conn.executemany(
        "INSERT OR REPLACE INTO facts (authority_code, quarter, dev_type, metric, value, source) VALUES (?,?,?,?,?,'pins')",
        ((r.code, r.quarter, r.dev_type, r.metric, float(r.value))
         for r in facts.itertuples(index=False)),
    )
    conn.commit()
    return cur.rowcount


def run(conn: sqlite3.Connection, offline: bool = False) -> int:
    cfg = sources_config()["pins_appeals"]["files"]
    frames = []
    for key in ("casework", "casework_older"):
        c = cfg[key]
        path = fetch(c["url"], c["filename"], offline=offline)
        log.info("parsing %s sheet '%s' (xlsx, slow)", path.name, c["sheet"])
        frames.append(parse_casework(path, c["sheet"]))
        log.info("%s: %d decided appeals", path.name, len(frames[-1]))
    appeals = pd.concat(frames, ignore_index=True)
    facts = aggregate(appeals)
    if len(facts) < 10_000:
        raise SourceError(f"Suspiciously few PINS fact rows ({len(facts)}) — check workbook layout.")
    return load(conn, facts)
