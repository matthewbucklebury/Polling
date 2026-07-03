"""Plain-English one-paragraph summary of an authority, generated from the data.

Statements are only made where the underlying denominator is big enough, and
each claim is relative to the distribution across active English authorities
in the same quarter (percentile bands, not arbitrary cutoffs)."""
from __future__ import annotations

import sqlite3


def _percentile(conn: sqlite3.Connection, metric: str, quarter: str, value: float) -> float | None:
    row = conn.execute(
        """SELECT SUM(CASE WHEN m.value <= ? THEN 1 ELSE 0 END) AS below, COUNT(*) AS n
           FROM metrics m JOIN authorities a ON a.code=m.authority_code
           WHERE m.metric=? AND m.quarter=? AND m.window='4Q' AND a.active=1""",
        (value, metric, quarter)).fetchone()
    if not row or not row["n"]:
        return None
    return 100.0 * row["below"] / row["n"]


def _band(p: float) -> str:
    if p < 20:
        return "well below average"
    if p < 40:
        return "below average"
    if p <= 60:
        return "around average"
    if p <= 80:
        return "above average"
    return "well above average"


def plain_english_summary(conn: sqlite3.Connection, authority: dict, latest: dict) -> str:
    name = authority["name"]
    parts: list[str] = []

    def latest_val(metric: str) -> tuple[str, float] | None:
        e = latest.get(metric)
        return (e["quarter"], e["value"]) if e else None

    ar = latest_val("approval_rate_major_res")
    den = latest_val("decisions_major_res")
    if ar and den and den[1] >= 10:
        p = _percentile(conn, "approval_rate_major_res", ar[0], ar[1])
        if p is not None:
            parts.append(
                f"{name} approves a share of major residential schemes that is {_band(p)} "
                f"({ar[1]:.0f}% over the year to {ar[0]})"
            )

    sp = latest_val("pct_intime_statutory_major")
    if sp:
        p = _percentile(conn, "pct_intime_statutory_major", sp[0], sp[1])
        if p is not None:
            parts.append(f"decides major applications {'quickly' if p > 60 else 'slowly' if p < 40 else 'at a typical pace'} "
                         f"on a statutory-time basis ({sp[1]:.0f}% within 13 weeks)")

    eot = latest_val("eot_share_all")
    if eot:
        p = _percentile(conn, "eot_share_all", eot[0], eot[1])
        if p is not None and (p < 25 or p > 75):
            parts.append(f"makes {'heavy' if p > 75 else 'light'} use of extension-of-time agreements "
                         f"({eot[1]:.0f}% of decisions)")

    ov = latest_val("overturn_rate")
    ovd = latest_val("appeals_decided")
    if ov and ovd and ovd[1] >= 8:
        p = _percentile(conn, "overturn_rate", ov[0], ov[1])
        if p is not None:
            parts.append(f"loses a share of appeals that is {_band(p)} ({ov[1]:.0f}% overturned)")

    hdt = conn.execute(
        "SELECT year, value FROM annual WHERE authority_code=? AND metric='hdt_measure' ORDER BY year DESC LIMIT 1",
        (authority["code"],)).fetchone()
    if hdt:
        v = hdt["value"]
        verdict = ("comfortably passed" if v >= 115 else "passed" if v >= 95 else
                   "fell short of" if v >= 75 else "failed")
        parts.append(f"{verdict} the {hdt['year']} Housing Delivery Test ({v:.0f}% of homes required)")

    if not parts:
        return f"Not enough recent data to characterise {name} — see the charts below."
    if len(parts) == 1:
        return parts[0] + "."
    return "; ".join(parts[:-1]) + "; and " + parts[-1] + "."
