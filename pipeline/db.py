"""SQLite schema and connection helpers shared by the pipeline (writer) and app (reader)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .common import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS authorities (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT,
    authority_type TEXT,
    ruc TEXT,
    population INTEGER,
    active INTEGER NOT NULL DEFAULT 1,
    successor_code TEXT
);

CREATE TABLE IF NOT EXISTS facts (
    authority_code TEXT NOT NULL,
    quarter TEXT NOT NULL,          -- 'YYYYQn'
    dev_type TEXT NOT NULL,         -- all|major|minor|other|major_res|minor_res|householder
    metric TEXT NOT NULL,
    value REAL,
    source TEXT NOT NULL,
    PRIMARY KEY (authority_code, quarter, dev_type, metric, source)
);
CREATE INDEX IF NOT EXISTS idx_facts_aq ON facts(authority_code, quarter);

CREATE TABLE IF NOT EXISTS metrics (
    authority_code TEXT NOT NULL,   -- GSS code, 'ENG', or 'REG:<region>'
    quarter TEXT NOT NULL,
    metric TEXT NOT NULL,
    window TEXT NOT NULL,           -- 'Q' or '4Q'
    value REAL,
    PRIMARY KEY (authority_code, quarter, metric, window)
);
CREATE INDEX IF NOT EXISTS idx_metrics_mq ON metrics(metric, window, quarter);
CREATE INDEX IF NOT EXISTS idx_metrics_a ON metrics(authority_code, metric, window);

CREATE TABLE IF NOT EXISTS annual (
    authority_code TEXT NOT NULL,
    year INTEGER NOT NULL,          -- financial year ending (2023 = 2022-23)
    metric TEXT NOT NULL,
    value REAL,
    PRIMARY KEY (authority_code, year, metric)
);

CREATE TABLE IF NOT EXISTS boundaries (
    authority_code TEXT PRIMARY KEY,
    geojson TEXT NOT NULL           -- one GeoJSON Feature (geometry only, WGS84)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    source TEXT NOT NULL,
    run_at TEXT NOT NULL,
    status TEXT NOT NULL,           -- ok | failed | skipped | sample
    message TEXT,
    rows_loaded INTEGER
);
"""


def connect(path: Path | None = None, *, readonly: bool = False) -> sqlite3.Connection:
    p = Path(path) if path else DB_PATH
    if readonly:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True, check_same_thread=False)
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(p)
        conn.executescript(SCHEMA)
        conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn
