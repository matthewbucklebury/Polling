"""Housing delivery context: MHCLG Live Table 122 (net additional dwellings) and
the Housing Delivery Test measurement. Both are annual, keyed by financial year
ending (2025 = 2024-25), and loaded into the `annual` table.

Government ODS quirks handled here: cover/notes sheets, headline rows several
rows down, note suffixes on year headers ('2004-05 [note 1]'), grouping rows
without codes, '[x]' for unavailable.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

from ..common import SourceError, log, sources_config
from ..common import download as fetch

FY_RE = re.compile(r"^(\d{4})-(\d{2})")


def _fy_end_year(header: str) -> int | None:
    """'2001-02' or '2024-25 [p]' -> 2002 / 2025."""
    m = FY_RE.match(str(header).strip())
    if not m:
        return None
    start = int(m.group(1))
    return start + 1


def parse_lt122(path: Path, min_records: int = 1000, min_years: int = 10) -> pd.DataFrame:
    """-> long frame (code, year, metric='net_additions', value). Includes England (E92000001)."""
    try:
        raw = pd.read_excel(path, engine="odf", sheet_name="LT_122", header=None)
    except ValueError as e:
        raise SourceError(f"{path.name}: cannot read sheet 'LT_122': {e}") from e

    header_idx = None
    for i in range(min(12, len(raw))):
        if any(str(c).strip() == "Current ONS code" for c in raw.iloc[i]):
            header_idx = i
            break
    if header_idx is None:
        raise SourceError(f"{path.name} sheet 'LT_122': header row with 'Current ONS code' not found")

    header = raw.iloc[header_idx].tolist()
    code_col = header.index("Current ONS code")
    year_cols = {j: _fy_end_year(h) for j, h in enumerate(header) if _fy_end_year(h)}
    if len(year_cols) < min_years:
        raise SourceError(f"{path.name} sheet 'LT_122': only {len(year_cols)} year columns recognised")

    body = raw.iloc[header_idx + 1:]
    records = []
    for _, row in body.iterrows():
        code = str(row[code_col]).strip()
        # LPA-level rows only: E06-E09. E10 counties / E12 regions / grouping rows
        # would double-count; England total (E92000001) is stored as 'ENG'.
        if code == "E92000001":
            code = "ENG"
        elif not re.match(r"^E0[6789]\d{6}$", code):
            continue
        for j, year in year_cols.items():
            val = pd.to_numeric(row[j], errors="coerce")
            if pd.notna(val):
                records.append((code, year, "net_additions", float(val)))
    if len(records) < min_records:
        raise SourceError(f"{path.name} sheet 'LT_122': only {len(records)} values parsed — layout change?")
    return pd.DataFrame(records, columns=["code", "year", "metric", "value"])


def parse_hdt(path: Path, min_records: int = 300) -> pd.DataFrame:
    """-> long frame (code, year, metric, value) for the HDT measurement year."""
    try:
        raw = pd.read_excel(path, engine="odf", sheet_name=0, header=None)
    except ValueError as e:
        raise SourceError(f"{path.name}: cannot read first sheet: {e}") from e

    title = " ".join(str(c) for c in raw.iloc[0] if pd.notna(c))
    m = re.search(r"(\d{4}) measurement", title)
    if not m:
        raise SourceError(f"{path.name}: cannot find measurement year in title {title!r}")
    year = int(m.group(1))

    header_idx = None
    for i in range(min(12, len(raw))):
        if str(raw.iloc[i, 0]).strip() == "ONS Code":
            header_idx = i
            break
    if header_idx is None:
        raise SourceError(f"{path.name}: header row starting 'ONS Code' not found")
    header = raw.iloc[header_idx].tolist()

    def col_like(pattern: str) -> int:
        for j, h in enumerate(header):
            if re.search(pattern, str(h), re.I):
                return j
        raise SourceError(f"{path.name}: no column matching {pattern!r} in {header}")

    c_req = col_like(r"total number of homes required")
    c_del = col_like(r"total number of homes delivered")
    c_measure = col_like(r"measurement$")

    records = []
    for _, row in raw.iloc[header_idx + 1:].iterrows():
        code = str(row[0]).strip()
        if not re.match(r"^E\d{8}$", code):
            continue
        req = pd.to_numeric(row[c_req], errors="coerce")
        dlv = pd.to_numeric(row[c_del], errors="coerce")
        measure = pd.to_numeric(row[c_measure], errors="coerce")
        if pd.notna(req):
            records.append((code, year, "hdt_required", float(req)))
        if pd.notna(dlv):
            records.append((code, year, "hdt_delivered", float(dlv)))
        if pd.notna(measure):
            # published as a ratio (1.0 = 100%); store as percent
            records.append((code, year, "hdt_measure", float(measure) * 100))
    if len(records) < min_records:
        raise SourceError(f"{path.name}: only {len(records)} HDT values parsed — layout change?")
    return pd.DataFrame(records, columns=["code", "year", "metric", "value"])


def load(conn: sqlite3.Connection, frames: list[pd.DataFrame]) -> int:
    df = pd.concat(frames, ignore_index=True)
    cur = conn.executemany(
        "INSERT OR REPLACE INTO annual (authority_code, year, metric, value) VALUES (?,?,?,?)",
        ((r.code, int(r.year), r.metric, float(r.value)) for r in df.itertuples(index=False)),
    )
    conn.commit()
    return cur.rowcount


def run(conn: sqlite3.Connection, offline: bool = False) -> int:
    cfg = sources_config()["housing_delivery"]["files"]
    frames = []
    path = fetch(cfg["net_additions"]["url"], cfg["net_additions"]["filename"], offline=offline)
    log.info("parsing %s", path.name)
    frames.append(parse_lt122(path))
    log.info("LT122: %d values", len(frames[-1]))
    path = fetch(cfg["hdt"]["url"], cfg["hdt"]["filename"], offline=offline)
    log.info("parsing %s", path.name)
    frames.append(parse_hdt(path))
    log.info("HDT: %d values", len(frames[-1]))
    return load(conn, frames)
