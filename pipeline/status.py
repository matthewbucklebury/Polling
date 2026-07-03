"""Record per-source pipeline outcomes in the DB and PIPELINE_STATUS.md."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from .common import ROOT

STATUS_PATH = ROOT / "PIPELINE_STATUS.md"


def record(conn: sqlite3.Connection, source: str, status: str, message: str = "", rows: int = 0) -> None:
    conn.execute(
        "INSERT INTO pipeline_runs (source, run_at, status, message, rows_loaded) VALUES (?,?,?,?,?)",
        (source, datetime.now(timezone.utc).isoformat(timespec="seconds"), status, message, rows),
    )
    conn.commit()


def latest_runs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT source, run_at, status, message, rows_loaded FROM pipeline_runs r
           WHERE run_at = (SELECT MAX(run_at) FROM pipeline_runs WHERE source = r.source)
           ORDER BY source"""
    ).fetchall()


def write_status_md(conn: sqlite3.Connection) -> None:
    rows = latest_runs(conn)
    icon = {"ok": "✅", "failed": "❌", "skipped": "⏭️", "sample": "🧪"}
    lines = [
        "# Pipeline status",
        "",
        f"_Last written {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by `python -m pipeline.cli`._",
        "",
    ]
    failures = [r for r in rows if r["status"] in ("failed", "sample")]
    if failures:
        lines += ["## ⚠️ Attention needed", ""]
        for r in failures:
            lines.append(f"- **{r['source']}** — {r['status']}: {r['message']}")
        lines.append("")
    lines += ["## Latest run per source", "", "| Source | Status | Rows | When (UTC) | Detail |", "|---|---|---:|---|---|"]
    for r in rows:
        lines.append(
            f"| {r['source']} | {icon.get(r['status'], '?')} {r['status']} | {r['rows_loaded'] or 0} "
            f"| {r['run_at']} | {(r['message'] or '').replace('|', '/')} |"
        )
    lines += [
        "",
        "If a download failed the most likely cause is a moved gov.uk asset URL: open the",
        "landing page listed in `config/sources.yml`, copy the new file URL into the config,",
        "and rerun `make pipeline` (cached raw files make partial reruns cheap).",
        "",
    ]
    STATUS_PATH.write_text("\n".join(lines))
