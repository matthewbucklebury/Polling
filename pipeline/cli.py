"""Pipeline CLI.

Usage:
    python -m pipeline.cli run                 # all sources, then derive metrics
    python -m pipeline.cli run --source pins_appeals
    python -m pipeline.cli run --offline       # parse from data/raw cache only
    python -m pipeline.cli status              # print latest per-source status
    python -m pipeline.cli reset               # drop the database file

A failing source never aborts the run: it is logged, recorded in PIPELINE_STATUS.md,
and (if it has never loaded) backfilled with clearly-marked sample data.
"""
from __future__ import annotations

import argparse
import logging
import sys

from . import metrics, sample_data, status
from .common import DB_PATH, SourceError, log
from .db import connect
from .sources import authority_meta, housing_delivery, mhclg_applications, pins_appeals

SOURCES = {
    "mhclg_applications": mhclg_applications.run,
    "pins_appeals": pins_appeals.run,
    "housing_delivery": housing_delivery.run,
    "authority_meta": authority_meta.run,
}
# authority_meta first: it seeds the authorities table others enrich.
ORDER = ["authority_meta", "mhclg_applications", "pins_appeals", "housing_delivery"]


def run(only: str | None = None, offline: bool = False) -> int:
    conn = connect()
    failed = []
    for name in ORDER:
        if only and name != only:
            continue
        log.info("=== source: %s ===", name)
        try:
            rows = SOURCES[name](conn, offline=offline)
            status.record(conn, name, "ok", rows=rows)
            log.info("=== %s: ok, %d rows ===", name, rows)
        except SourceError as e:
            log.error("=== %s FAILED: %s ===", name, e)
            status.record(conn, name, "failed", str(e))
            failed.append(name)
        except Exception as e:  # noqa: BLE001 - keep building whatever we can overnight
            log.exception("=== %s CRASHED ===", name)
            status.record(conn, name, "failed", f"unexpected error: {e}")
            failed.append(name)

    if not only or failed:
        sample_data.backfill_missing(conn)
    if not only or only not in ("authority_meta",):
        log.info("=== deriving metrics ===")
        metrics.derive_all(conn)
    status.write_status_md(conn)
    conn.commit()
    conn.close()
    if failed:
        log.warning("Completed with failures: %s (see PIPELINE_STATUS.md)", ", ".join(failed))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run", help="fetch, parse, load, derive")
    p_run.add_argument("--source", choices=sorted(SOURCES), help="run a single source")
    p_run.add_argument("--offline", action="store_true", help="use data/raw cache, no network")
    sub.add_parser("status", help="print latest per-source status")
    sub.add_parser("reset", help="delete the database file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    if args.cmd == "run":
        return run(only=args.source, offline=args.offline)
    if args.cmd == "status":
        conn = connect()
        for r in status.latest_runs(conn):
            print(f"{r['source']:<22} {r['status']:<8} rows={r['rows_loaded'] or 0:<8} {r['run_at']}  {r['message'] or ''}")
        return 0
    if args.cmd == "reset":
        if DB_PATH.exists():
            DB_PATH.unlink()
            print(f"deleted {DB_PATH}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
