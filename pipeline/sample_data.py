"""Deterministic sample data for sources that have never loaded.

If a download is dead overnight the app must still wake up runnable. For any
logical dataset with no rows at all, this module generates clearly-marked
synthetic data (facts tagged source='sample', a 'sample' row in pipeline_runs,
and a banner in the app). Real data always wins: sample rows are only created
when a dataset is empty, and are deleted the next time the real source loads.
"""
from __future__ import annotations

import json
import sqlite3

import numpy as np

from .common import log
from .quarters import seq_quarter
from .status import record

SAMPLE_QUARTERS = [seq_quarter(s) for s in range(2015 * 4, 2026 * 4)]  # 2015Q1..2026Q4
SAMPLE_AUTHORITIES = [
    (f"SAMPLE{i:03d}", f"Sampleshire {name}", region, "district")
    for i, (name, region) in enumerate(
        [("Northgate", "North West"), ("Eastfield", "East of England"), ("Weston", "South West"),
         ("Southdown", "South East"), ("Midvale", "West Midlands"), ("Kirkby", "Yorkshire and the Humber"),
         ("Harborough", "East Midlands"), ("Tyneside", "North East"), ("Riverside", "London"),
         ("Fenland", "East of England"), ("Moorland", "North West"), ("Downs", "South East")],
        start=1,
    )
]


def _authorities(conn: sqlite3.Connection) -> list[str]:
    codes = [r[0] for r in conn.execute(
        "SELECT code FROM authorities WHERE active=1 AND code LIKE 'E0%' ORDER BY code")]
    if codes:
        return codes
    log.warning("authorities table empty — creating %d sample authorities", len(SAMPLE_AUTHORITIES))
    for code, name, region, atype in SAMPLE_AUTHORITIES:
        conn.execute(
            "INSERT OR IGNORE INTO authorities (code, name, region, authority_type, active) VALUES (?,?,?,?,1)",
            (code, name, region, atype),
        )
    return [a[0] for a in SAMPLE_AUTHORITIES]


def _sample_mhclg(conn: sqlite3.Connection, codes: list[str]) -> int:
    rng = np.random.default_rng(42)
    rows = []
    for code in codes:
        base = rng.uniform(0.75, 0.95)          # authority-level approval propensity
        speed = rng.uniform(0.5, 0.95)
        vol = rng.integers(80, 600)
        for q in SAMPLE_QUARTERS:
            for dt, share in [("all", 1.0), ("major", 0.05), ("minor", 0.3), ("other", 0.65),
                              ("major_res", 0.03), ("minor_res", 0.2), ("householder", 0.4)]:
                d = max(1, int(vol * share * rng.uniform(0.8, 1.2)))
                g = int(d * min(1, base + rng.normal(0, 0.05) - (0.15 if "major" in dt else 0)))
                g = max(0, min(d, g))
                pa = int(d * rng.uniform(0.2, 0.5))
                expa = d - pa
                intime_expa = int(expa * min(1, speed + rng.normal(0, 0.05)))
                rows += [
                    (code, q, dt, "decisions", d), (code, q, dt, "granted", g),
                    (code, q, dt, "refused", d - g),
                    (code, q, dt, "decisions_pa", pa), (code, q, dt, "intime_pa", int(pa * 0.9)),
                ]
                if dt in ("all", "major", "minor", "other"):
                    rows += [(code, q, dt, "decisions_expa", expa), (code, q, dt, "intime_expa", intime_expa)]
                else:
                    b1 = int(intime_expa * 0.7)
                    rows += [(code, q, dt, "band1", b1), (code, q, dt, "band2", intime_expa - b1),
                             (code, q, dt, "band3", max(0, expa - intime_expa)),
                             (code, q, dt, "band4", 0), (code, q, dt, "band5", 0), (code, q, dt, "band6", 0)]
            rows += [(code, q, "all", "received", int(vol * rng.uniform(0.9, 1.3))),
                     (code, q, "all", "withdrawn", int(vol * 0.05))]
    conn.executemany(
        "INSERT OR REPLACE INTO facts (authority_code, quarter, dev_type, metric, value, source) VALUES (?,?,?,?,?,'sample')",
        rows,
    )
    return len(rows)


def _sample_pins(conn: sqlite3.Connection, codes: list[str]) -> int:
    rng = np.random.default_rng(43)
    rows = []
    for code in codes:
        overturn = rng.uniform(0.15, 0.45)
        for q in SAMPLE_QUARTERS:
            decided = int(rng.integers(2, 25))
            allowed = int(decided * min(1, max(0, overturn + rng.normal(0, 0.08))))
            split = int(decided > 10)
            rows += [
                (code, q, "all", "appeals_decided", decided),
                (code, q, "all", "appeals_allowed", allowed),
                (code, q, "all", "appeals_dismissed", decided - allowed - split),
                (code, q, "all", "appeals_split", split),
                (code, q, "all", "appeals_refusal_decided", int(decided * 0.9)),
                (code, q, "all", "appeals_refusal_allowed", int(allowed * 0.9)),
            ]
    conn.executemany(
        "INSERT OR REPLACE INTO facts (authority_code, quarter, dev_type, metric, value, source) VALUES (?,?,?,?,?,'sample')",
        rows,
    )
    return len(rows)


def _sample_housing(conn: sqlite3.Connection, codes: list[str]) -> int:
    rng = np.random.default_rng(44)
    rows = []
    for code in codes:
        target = int(rng.integers(200, 1500))
        for year in range(2015, 2026):
            rows.append((code, year, "net_additions", int(target * rng.uniform(0.5, 1.4))))
        rows += [(code, 2023, "hdt_required", target * 3),
                 (code, 2023, "hdt_delivered", int(target * 3 * rng.uniform(0.5, 1.4)))]
        rows.append((code, 2023, "hdt_measure", round(rows[-1][3] / (target * 3) * 100, 1)))
    conn.executemany(
        "INSERT OR REPLACE INTO annual (authority_code, year, metric, value) VALUES (?,?,?,?)", rows)
    return len(rows)


def _sample_boundaries(conn: sqlite3.Connection, codes: list[str]) -> int:
    """Placeholder tile grid over the rough extent of England so the map renders."""
    cols = 16
    rows_written = 0
    for i, code in enumerate(sorted(codes)):
        x = -5.5 + (i % cols) * 0.45
        y = 50.2 + (i // cols) * 0.35
        ring = [[x, y], [x + 0.4, y], [x + 0.4, y + 0.3], [x, y + 0.3], [x, y]]
        feature = {"type": "Feature", "properties": {"code": code, "sample": True},
                   "geometry": {"type": "Polygon", "coordinates": [ring]}}
        conn.execute("INSERT OR REPLACE INTO boundaries (authority_code, geojson) VALUES (?,?)",
                     (code, json.dumps(feature)))
        rows_written += 1
    return rows_written


def backfill_missing(conn: sqlite3.Connection) -> None:
    """Generate sample rows for any dataset that is completely empty."""
    codes = _authorities(conn)
    checks = [
        ("mhclg_applications", "SELECT 1 FROM facts WHERE source IN ('ps1','ps2') LIMIT 1", _sample_mhclg),
        ("pins_appeals", "SELECT 1 FROM facts WHERE source='pins' LIMIT 1", _sample_pins),
        ("housing_delivery", "SELECT 1 FROM annual LIMIT 1", _sample_housing),
        ("authority_meta", "SELECT 1 FROM boundaries LIMIT 1", _sample_boundaries),
    ]
    for source, probe, generator in checks:
        if conn.execute(probe).fetchone():
            continue
        n = generator(conn, codes)
        log.warning("%s: no real data — generated %d SAMPLE rows", source, n)
        record(conn, source, "sample", "no real data loaded; generated synthetic sample data", n)
    conn.commit()
