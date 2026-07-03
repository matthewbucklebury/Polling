"""JSON API. Read-only over the SQLite database the pipeline builds."""
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Query, Response

from pipeline.common import DB_PATH, settings
from . import catalog
from .summary import plain_english_summary

router = APIRouter(prefix="/api")


def db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise HTTPException(503, "Database not built yet — run `make pipeline` first.")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def rows(conn, sql, params=()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


@router.get("/meta")
def meta():
    conn = db()
    try:
        cfg = settings()
        # Quarters where the core MHCLG data exists (appeals can run a quarter ahead,
        # which would otherwise offer empty map/league views).
        quarters = [r["quarter"] for r in conn.execute(
            "SELECT DISTINCT quarter FROM metrics WHERE authority_code='ENG' AND metric='approval_rate_all' ORDER BY quarter")]
        display_from = cfg["app"].get("display_from_quarter", "2004Q2")
        runs = rows(conn, """SELECT source, status, message, run_at, rows_loaded FROM pipeline_runs r
                             WHERE run_at = (SELECT MAX(run_at) FROM pipeline_runs WHERE source = r.source)""")
        regions = [r["region"] for r in conn.execute(
            "SELECT DISTINCT region FROM authorities WHERE active=1 AND region IS NOT NULL ORDER BY region")]
        types = [r["authority_type"] for r in conn.execute(
            "SELECT DISTINCT authority_type FROM authorities WHERE active=1 AND authority_type IS NOT NULL ORDER BY 1")]
        rucs = [r["ruc"] for r in conn.execute(
            "SELECT DISTINCT ruc FROM authorities WHERE active=1 AND ruc IS NOT NULL ORDER BY 1")]
        return {
            "quarters": [q for q in quarters if q >= display_from],
            "all_quarters": quarters,
            "latest_quarter": quarters[-1] if quarters else None,
            "metrics": catalog.METRICS,
            "annual_metrics": catalog.ANNUAL_METRICS,
            "rankable": catalog.RANKABLE,
            "regions": regions,
            "authority_types": types,
            "rucs": rucs,
            "friction": cfg["friction_score"],
            "league_defaults": cfg["league_tables"],
            "pipeline": runs,
            "sample_sources": [r["source"] for r in runs if r["status"] == "sample"],
        }
    finally:
        conn.close()


@router.get("/authorities")
def authorities():
    conn = db()
    try:
        latest = conn.execute("SELECT MAX(quarter) FROM metrics WHERE metric='friction_score'").fetchone()[0]
        friction = {r["authority_code"]: r["value"] for r in conn.execute(
            "SELECT authority_code, value FROM metrics WHERE metric='friction_score' AND window='4Q' AND quarter=?",
            (latest,))}
        auths = rows(conn, """SELECT code, name, region, authority_type, ruc, population
                              FROM authorities WHERE active=1 ORDER BY name""")
        for a in auths:
            a["friction_score"] = friction.get(a["code"])
        return {"latest_friction_quarter": latest, "authorities": auths}
    finally:
        conn.close()


def _series(conn, code: str, metrics: list[str], window: str) -> dict[str, list]:
    out = defaultdict(list)
    qmarks = ",".join("?" * len(metrics))
    for r in conn.execute(
        f"""SELECT metric, quarter, value FROM metrics
            WHERE authority_code=? AND window=? AND metric IN ({qmarks}) ORDER BY quarter""",
        (code, window, *metrics),
    ):
        out[r["metric"]].append({"q": r["quarter"], "v": r["value"]})
    return dict(out)


@router.get("/authorities/{code}")
def authority_profile(code: str):
    conn = db()
    try:
        a = conn.execute("SELECT * FROM authorities WHERE code=?", (code,)).fetchone()
        if not a:
            raise HTTPException(404, f"Unknown authority {code}")
        a = dict(a)
        display_from = settings()["app"].get("display_from_quarter", "2004Q2")

        profile_metrics = [
            "approval_rate_all", "approval_rate_major_res", "approval_rate_minor_res", "approval_rate_householder",
            "pct_intime_headline_major", "pct_intime_statutory_major", "pct_intime_headline_minor",
            "pct_intime_statutory_minor", "eot_share_all", "eot_gap_major",
            "received_all", "decisions_all", "decisions_major_res", "decisions_vs_5yr",
            "overturn_rate", "refusal_overturn_rate", "appeal_rate_refusals", "appeals_decided",
            "friction_score", "friction_approval_rate_major_res",
            "friction_pct_intime_statutory_major", "friction_overturn_rate",
        ]
        region_code = f"REG:{a['region']}" if a.get("region") else None
        series = {"authority": _series(conn, code, profile_metrics, "4Q"),
                  "england": _series(conn, "ENG", profile_metrics, "4Q")}
        if region_code:
            series["region"] = _series(conn, region_code, profile_metrics, "4Q")
        for s in series.values():
            for m, pts in s.items():
                s[m] = [p for p in pts if p["q"] >= display_from]

        annual = rows(conn, "SELECT year, metric, value FROM annual WHERE authority_code=? ORDER BY year", (code,))
        annual_eng = rows(conn, "SELECT year, metric, value FROM annual WHERE authority_code='ENG' ORDER BY year")

        latest = {}
        for r in conn.execute(
            """SELECT metric, quarter, value FROM metrics m
               WHERE authority_code=? AND window='4Q'
                 AND quarter=(SELECT MAX(quarter) FROM metrics WHERE authority_code=? AND metric=m.metric AND window='4Q')""",
            (code, code)):
            latest[r["metric"]] = {"quarter": r["quarter"], "value": r["value"]}

        summary = plain_english_summary(conn, a, latest)
        return {"authority": a, "series": series, "annual": annual, "annual_england": annual_eng,
                "latest": latest, "summary": summary}
    finally:
        conn.close()


@router.get("/map")
def map_values(metric: str, quarter: str, window: str = "4Q"):
    if metric not in catalog.METRICS:
        raise HTTPException(400, f"Unknown metric {metric}")
    conn = db()
    try:
        vals = {r["authority_code"]: r["value"] for r in conn.execute(
            """SELECT m.authority_code, m.value FROM metrics m
               JOIN authorities a ON a.code = m.authority_code
               WHERE m.metric=? AND m.quarter=? AND m.window=? AND a.active=1""",
            (metric, quarter, window))}
        return {"metric": metric, "quarter": quarter, "window": window, "values": vals}
    finally:
        conn.close()


@router.get("/geojson")
def geojson():
    conn = db()
    try:
        features = [json.loads(r["geojson"]) for r in conn.execute("SELECT geojson FROM boundaries")]
        return Response(
            json.dumps({"type": "FeatureCollection", "features": features}),
            media_type="application/geo+json",
            headers={"Cache-Control": "max-age=86400"},
        )
    finally:
        conn.close()


@router.get("/league")
def league(metric: str, quarter: str, window: str = "4Q", region: str | None = None,
           authority_type: str | None = None, ruc: str | None = None,
           min_denominator: int | None = None):
    if metric not in catalog.METRICS:
        raise HTTPException(400, f"Unknown metric {metric}")
    conn = db()
    try:
        den = catalog.MIN_DENOMINATORS.get(metric)
        min_den = min_denominator
        if den and min_den is None:
            min_den = settings()["league_tables"].get(den[1], 0)

        sql = """SELECT a.code, a.name, a.region, a.authority_type, a.ruc, m.value
                 FROM metrics m JOIN authorities a ON a.code=m.authority_code
                 WHERE m.metric=? AND m.quarter=? AND m.window=? AND a.active=1"""
        params: list = [metric, quarter, window]
        if region:
            sql += " AND a.region=?"; params.append(region)
        if authority_type:
            sql += " AND a.authority_type=?"; params.append(authority_type)
        if ruc:
            sql += " AND a.ruc LIKE ?"; params.append(f"{ruc}%")
        entries = rows(conn, sql, params)

        denominators = {}
        if den:
            denominators = {r["authority_code"]: r["value"] for r in conn.execute(
                "SELECT authority_code, value FROM metrics WHERE metric=? AND quarter=? AND window=?",
                (den[0], quarter, window))}
        out, excluded = [], 0
        for e in entries:
            d = denominators.get(e["code"]) if den else None
            e["denominator"] = d
            if den and min_den and (d is None or d < min_den):
                excluded += 1
                continue
            out.append(e)
        higher_is = catalog.METRICS[metric]["higher_is"]
        out.sort(key=lambda e: e["value"], reverse=(higher_is != "bad"))
        for i, e in enumerate(out, 1):
            e["rank"] = i
        eng = conn.execute(
            "SELECT value FROM metrics WHERE authority_code='ENG' AND metric=? AND quarter=? AND window=?",
            (metric, quarter, window)).fetchone()
        return {"metric": metric, "quarter": quarter, "window": window,
                "min_denominator": min_den, "denominator_metric": den[0] if den else None,
                "excluded_below_threshold": excluded, "england": eng["value"] if eng else None,
                "entries": out}
    finally:
        conn.close()


@router.get("/compare")
def compare(codes: str, metric: str, window: str = "4Q"):
    code_list = [c.strip() for c in codes.split(",") if c.strip()][:5]
    if metric not in catalog.METRICS:
        raise HTTPException(400, f"Unknown metric {metric}")
    conn = db()
    try:
        display_from = settings()["app"].get("display_from_quarter", "2004Q2")
        out = {}
        for c in code_list + ["ENG"]:
            pts = _series(conn, c, [metric], window).get(metric, [])
            out[c] = [p for p in pts if p["q"] >= display_from]
        names = {r["code"]: r["name"] for r in conn.execute(
            f"SELECT code, name FROM authorities WHERE code IN ({','.join('?'*len(code_list))})", code_list)}
        names["ENG"] = "England"
        return {"metric": metric, "window": window, "series": out, "names": names}
    finally:
        conn.close()


@router.get("/national")
def national():
    conn = db()
    try:
        display_from = settings()["app"].get("display_from_quarter", "2004Q2")
        metric_list = [
            "received_all", "decisions_all", "granted_all", "approval_rate_all",
            "approval_rate_major_res", "eot_share_all", "eot_share_major",
            "pct_intime_headline_major", "pct_intime_statutory_major",
            "pct_intime_headline_minor", "pct_intime_statutory_minor",
            "overturn_rate", "appeals_decided", "refusal_overturn_rate",
        ]
        series = _series(conn, "ENG", metric_list, "4Q")
        series_q = _series(conn, "ENG", ["received_all", "decisions_all"], "Q")
        for s in (series, series_q):
            for m, pts in s.items():
                s[m] = [p for p in pts if p["q"] >= display_from]
        annual = rows(conn, "SELECT year, metric, value FROM annual WHERE authority_code='ENG' ORDER BY year")
        return {"series_4q": series, "series_q": series_q, "annual": annual}
    finally:
        conn.close()
