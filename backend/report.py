"""Self-contained HTML report for one authority: everything inlined (styles +
SVG charts rendered server-side), so the file can be saved, emailed or printed
to PDF with no external requests."""
from __future__ import annotations

import html
from datetime import date

from fastapi import APIRouter, HTTPException, Response

from .api import authority_profile, db
from . import catalog

router = APIRouter(prefix="/api")


def _svg_line(series: dict[str, list], labels: dict[str, str], unit: str,
              width: int = 640, height: int = 200) -> str:
    """Tiny dependency-free multi-line SVG chart."""
    colors = ["#1d4ed8", "#9333ea", "#94a3b8", "#059669", "#dc2626"]
    pts_all = [p for s in series.values() for p in s]
    if not pts_all:
        return "<p class='nodata'>No data.</p>"
    quarters = sorted({p["q"] for p in pts_all})
    vmin = min(p["v"] for p in pts_all)
    vmax = max(p["v"] for p in pts_all)
    if unit == "%":
        vmin, vmax = min(vmin, 0), max(vmax, 100)
    if vmax == vmin:
        vmax = vmin + 1
    pad_l, pad_r, pad_t, pad_b = 42, 8, 8, 22
    iw, ih = width - pad_l - pad_r, height - pad_t - pad_b
    qx = {q: pad_l + iw * i / max(1, len(quarters) - 1) for i, q in enumerate(quarters)}

    def y(v):
        return pad_t + ih * (1 - (v - vmin) / (vmax - vmin))

    out = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           'style="font:10px sans-serif;background:#fff">']
    for frac in (0, 0.5, 1):
        v = vmin + (vmax - vmin) * frac
        out.append(f'<line x1="{pad_l}" y1="{y(v):.1f}" x2="{width-pad_r}" y2="{y(v):.1f}" stroke="#e2e8f0"/>')
        out.append(f'<text x="{pad_l-4}" y="{y(v)+3:.1f}" text-anchor="end" fill="#64748b">{v:,.0f}</text>')
    step = max(1, len(quarters) // 6)
    for q in quarters[::step]:
        out.append(f'<text x="{qx[q]:.1f}" y="{height-6}" text-anchor="middle" fill="#64748b">{q}</text>')
    legend_x = pad_l
    for i, (key, pts) in enumerate(series.items()):
        if not pts:
            continue
        c = colors[i % len(colors)]
        path = " ".join(f"{'M' if j == 0 else 'L'}{qx[p['q']]:.1f},{y(p['v']):.1f}" for j, p in enumerate(pts))
        out.append(f'<path d="{path}" fill="none" stroke="{c}" stroke-width="{2 if i == 0 else 1.2}"/>')
        label = html.escape(labels.get(key, key))
        out.append(f'<rect x="{legend_x}" y="{pad_t}" width="8" height="8" fill="{c}"/>'
                   f'<text x="{legend_x+11}" y="{pad_t+8}" fill="#334155">{label}</text>')
        legend_x += 11 + 6 * len(label) + 18
    out.append("</svg>")
    return "".join(out)


@router.get("/authorities/{code}/report")
def report(code: str):
    data = authority_profile(code)
    a = data["authority"]
    if not a:
        raise HTTPException(404)
    s = data["series"]
    labels = {"authority": a["name"], "region": a.get("region") or "Region", "england": "England"}

    def chart(metric: str) -> str:
        unit = catalog.METRICS.get(metric, {}).get("unit", "")
        series = {k: v.get(metric, []) for k, v in s.items()}
        return _svg_line(series, labels, unit)

    def latest_cell(metric: str) -> str:
        e = data["latest"].get(metric)
        if not e:
            return "–"
        unit = catalog.METRICS.get(metric, {}).get("unit", "")
        suffix = "%" if unit == "%" else (" pp" if unit == "pp" else "")
        return f"{e['value']:,.1f}{suffix} <span class='q'>({e['quarter']}, 4Q)</span>"

    key_metrics = [
        "approval_rate_all", "approval_rate_major_res", "pct_intime_headline_major",
        "pct_intime_statutory_major", "eot_share_all", "overturn_rate",
        "refusal_overturn_rate", "friction_score",
    ]
    stat_rows = "".join(
        f"<tr><td>{html.escape(catalog.METRICS[m]['label'])}</td><td>{latest_cell(m)}</td></tr>"
        for m in key_metrics
    )
    hdt = [r for r in data["annual"] if r["metric"] == "hdt_measure"]
    net = [r for r in data["annual"] if r["metric"] == "net_additions"]
    net_series = {"authority": [{"q": str(r["year"]), "v": r["value"]} for r in net]}
    delivery_html = _svg_line(net_series, {"authority": "Net additional dwellings"}, "count")
    hdt_html = (f"<p>Housing Delivery Test {hdt[-1]['year']}: <strong>{hdt[-1]['value']:.0f}%</strong> "
                "of homes required.</p>" if hdt else "<p class='nodata'>No HDT result loaded.</p>")

    charts = [
        ("Approval rate — major residential (4Q rolling)", chart("approval_rate_major_res")),
        ("Approval rate — all applications (4Q rolling)", chart("approval_rate_all")),
        ("Major decisions in time — headline (4Q rolling)", chart("pct_intime_headline_major")),
        ("Major decisions within statutory 13 weeks (4Q rolling)", chart("pct_intime_statutory_major")),
        ("Share of decisions under extension agreements (4Q rolling)", chart("eot_share_all")),
        ("Appeals overturn rate (4Q rolling)", chart("overturn_rate")),
        ("Applications decided (4Q rolling)", chart("decisions_all")),
    ]
    charts_html = "".join(f"<h3>{html.escape(t)}</h3>{c}" for t, c in charts)

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>{html.escape(a['name'])} — planning performance report</title>
<style>
body{{font:14px/1.5 -apple-system,'Segoe UI',sans-serif;color:#0f172a;max-width:720px;margin:2rem auto;padding:0 1rem}}
h1{{font-size:1.5rem;margin-bottom:.2rem}} h3{{margin:1.4rem 0 .4rem;font-size:1rem}}
.meta{{color:#64748b;margin:0 0 1rem}} .summary{{background:#f1f5f9;border-left:4px solid #1d4ed8;padding:.8rem 1rem;border-radius:0 6px 6px 0}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}} td{{border-bottom:1px solid #e2e8f0;padding:.35rem .5rem}}
td:last-child{{text-align:right;font-variant-numeric:tabular-nums}} .q{{color:#94a3b8;font-size:.85em}}
.nodata{{color:#94a3b8}} footer{{margin-top:2rem;color:#94a3b8;font-size:.8rem;border-top:1px solid #e2e8f0;padding-top:.6rem}}
@media print{{body{{margin:0}}}}
</style></head><body>
<h1>{html.escape(a['name'])}</h1>
<p class="meta">{html.escape(a.get('region') or '')} · {html.escape((a.get('authority_type') or '').replace('_',' '))}
 · {html.escape(a.get('ruc') or 'rural/urban class unknown')}
 {f"· population {a['population']:,}" if a.get('population') else ''}</p>
<p class="summary">{html.escape(data['summary'])}</p>
<h3>Key figures (rolling year)</h3>
<table>{stat_rows}</table>
{charts_html}
<h3>Housing delivery</h3>
{hdt_html}
{delivery_html}
<footer>Generated {date.today().isoformat()} by the UK Planning Applications Tracker.
Sources: MHCLG planning application statistics (PS1/PS2), Planning Inspectorate casework database,
MHCLG Live Table 122 and Housing Delivery Test, ONS Open Geography. Rolling-annual (4Q) figures;
see the in-app data dictionary for caveats (extension-of-time distortion, COVID-era anomalies,
reorganisation breaks in series).</footer>
</body></html>"""
    return Response(page, media_type="text/html",
                    headers={"Content-Disposition": f'inline; filename="{code}_planning_report.html"'})
