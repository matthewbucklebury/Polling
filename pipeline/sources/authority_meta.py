"""Authority metadata: ONS boundaries + rural/urban classification, and population.

One ArcGIS query against the ONS Open Geography portal returns generalised LAD
boundaries already joined to the 2021 Rural-Urban Classification. Population
comes from NOMIS mid-year estimates and is optional — the app degrades to
showing no population if it is unavailable.

Region names are filled in by the MHCLG source (PS files carry a Region column),
so this source only needs geometry + RUC + population.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from ..common import SourceError, log, sources_config
from ..common import download as fetch


def parse_boundaries(path: Path, min_features: int = 250) -> list[tuple[str, str, str, str]]:
    """GeoJSON -> [(code, name, ruc_name, feature_json)]."""
    try:
        gj = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise SourceError(f"{path.name}: not valid JSON ({e}) — ArcGIS may have returned an error page") from e
    feats = gj.get("features") or []
    if len(feats) < min_features:
        raise SourceError(f"{path.name}: only {len(feats)} features — expected ~296 English LADs")
    out = []
    for f in feats:
        props = f.get("properties", {})
        code, name = props.get("LAD24CD"), props.get("LAD24NM")
        if not code or not f.get("geometry"):
            raise SourceError(f"{path.name}: feature missing LAD24CD or geometry — field list changed?")
        ruc = props.get("RUC21NM") or props.get("Urban_rura") or None
        feature = {"type": "Feature", "properties": {"code": code, "name": name}, "geometry": f["geometry"]}
        out.append((code, name, ruc, json.dumps(feature, separators=(",", ":"))))
    return out


def parse_population(path: Path) -> dict[str, int]:
    df = pd.read_csv(path)
    cols = {c.upper(): c for c in df.columns}
    if "GEOGRAPHY_CODE" not in cols or "OBS_VALUE" not in cols:
        raise SourceError(f"{path.name}: expected GEOGRAPHY_CODE/OBS_VALUE columns, got {list(df.columns)}")
    df = df.dropna(subset=[cols["OBS_VALUE"]])
    return {str(r[cols["GEOGRAPHY_CODE"]]).strip(): int(r[cols["OBS_VALUE"]]) for _, r in df.iterrows()}


def run(conn: sqlite3.Connection, offline: bool = False) -> int:
    cfg = sources_config()["authority_meta"]["files"]

    path = fetch(cfg["boundaries"]["url"], cfg["boundaries"]["filename"], offline=offline)
    log.info("parsing %s", path.name)
    rows = parse_boundaries(path)
    conn.execute("DELETE FROM boundaries")
    for code, name, ruc, feature in rows:
        conn.execute(
            "INSERT INTO authorities (code, name, ruc) VALUES (?,?,?) "
            "ON CONFLICT(code) DO UPDATE SET ruc=excluded.ruc",
            (code, name, ruc),
        )
        conn.execute("INSERT OR REPLACE INTO boundaries (authority_code, geojson) VALUES (?,?)", (code, feature))
    n = len(rows)
    log.info("boundaries: %d features", n)

    # Population is optional: log and continue on failure.
    try:
        p = fetch(cfg["population"]["url"], cfg["population"]["filename"], offline=offline)
        pop = parse_population(p)
        for code, value in pop.items():
            conn.execute("UPDATE authorities SET population=? WHERE code=?", (value, code))
        log.info("population: %d authorities", len(pop))
        n += len(pop)
    except SourceError as e:
        log.warning("population skipped (optional): %s", e)

    conn.commit()
    return n
