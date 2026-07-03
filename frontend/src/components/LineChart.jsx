import { useMemo, useRef, useState } from 'react';
import { fmtValue } from '../api.js';

const SERIES_VARS = ['--series-1', '--series-5', '--muted', '--series-2', '--series-3', '--series-6'];

/**
 * Multi-series line chart. series = [{ key, label, points: [{q, v}], colorVar?, dashed? }]
 * x values (q) are ordinal quarter strings shared across series.
 */
export default function LineChart({ series, unit = '', height = 240, domain }) {
  const wrapRef = useRef(null);
  const [hover, setHover] = useState(null);
  const width = 640;
  const pad = { l: 44, r: 10, t: 10, b: 24 };

  const { quarters, vmin, vmax } = useMemo(() => {
    const qs = [...new Set(series.flatMap((s) => s.points.map((p) => p.q)))].sort();
    const vals = series.flatMap((s) => s.points.map((p) => p.v)).filter((v) => v != null);
    let lo = Math.min(...vals), hi = Math.max(...vals);
    if (domain) { lo = domain[0]; hi = domain[1]; }
    else {
      if (unit === '%') { lo = Math.min(lo, 0); hi = Math.max(hi, 100); }
      else { lo = Math.min(lo, 0); hi = hi * 1.05; }
      if (hi === lo) hi = lo + 1;
    }
    return { quarters: qs, vmin: lo, vmax: hi };
  }, [series, unit, domain]);

  if (!quarters.length) return <p className="sub">No data available.</p>;

  const iw = width - pad.l - pad.r, ih = height - pad.t - pad.b;
  const x = (q) => pad.l + (quarters.indexOf(q) / Math.max(1, quarters.length - 1)) * iw;
  const y = (v) => pad.t + ih * (1 - (v - vmin) / (vmax - vmin));
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => vmin + f * (vmax - vmin));
  const xStep = Math.max(1, Math.floor(quarters.length / 6));

  const onMove = (e) => {
    const rect = wrapRef.current.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * width;
    const idx = Math.round(((px - pad.l) / iw) * (quarters.length - 1));
    if (idx < 0 || idx >= quarters.length) return setHover(null);
    const q = quarters[idx];
    setHover({
      q,
      px: ((x(q) / width) * rect.width),
      values: series
        .map((s) => ({ label: s.label, colorVar: s.colorVar, v: s.points.find((p) => p.q === q)?.v }))
        .filter((s) => s.v != null),
    });
  };

  return (
    <div ref={wrapRef} style={{ position: 'relative' }} onMouseLeave={() => setHover(null)}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: '100%', height: 'auto', display: 'block' }}
        onMouseMove={onMove}
        role="img"
      >
        {ticks.map((t) => (
          <g key={t}>
            <line x1={pad.l} x2={width - pad.r} y1={y(t)} y2={y(t)} style={{ stroke: 'var(--grid)', strokeWidth: 1 }} />
            <text x={pad.l - 5} y={y(t) + 3.5} textAnchor="end" style={{ fill: 'var(--muted)', fontSize: 10 }}>
              {unit === '%' || unit === 'pp' ? `${Math.round(t)}` : t >= 1000 ? `${Math.round(t / 1000)}k` : Math.round(t)}
            </text>
          </g>
        ))}
        {quarters.filter((_, i) => i % xStep === 0).map((q) => (
          <text key={q} x={x(q)} y={height - 7} textAnchor="middle" style={{ fill: 'var(--muted)', fontSize: 10 }}>
            {q}
          </text>
        ))}
        {series.map((s, i) => {
          const pts = s.points.filter((p) => p.v != null);
          if (!pts.length) return null;
          const d = pts.map((p, j) => `${j ? 'L' : 'M'}${x(p.q).toFixed(1)},${y(p.v).toFixed(1)}`).join(' ');
          const color = `var(${s.colorVar || SERIES_VARS[i % SERIES_VARS.length]})`;
          return (
            <path
              key={s.key || s.label}
              d={d}
              fill="none"
              style={{ stroke: color, strokeWidth: i === 0 ? 2.2 : 1.6, strokeDasharray: s.dashed ? '5 4' : 'none' }}
            />
          );
        })}
        {hover && (
          <line
            x1={x(hover.q)} x2={x(hover.q)} y1={pad.t} y2={height - pad.b}
            style={{ stroke: 'var(--baseline)', strokeWidth: 1 }}
          />
        )}
      </svg>
      {series.length > 1 && (
        <div className="legend">
          {series.map((s, i) => (
            <span key={s.key || s.label}>
              <span className="swatch" style={{ background: `var(${s.colorVar || SERIES_VARS[i % SERIES_VARS.length]})` }} />
              {s.label}
            </span>
          ))}
        </div>
      )}
      {hover && hover.values.length > 0 && (
        <div
          className="chart-tooltip"
          style={{ left: Math.min(hover.px + 10, wrapRef.current.clientWidth - 180), top: 8 }}
        >
          <strong>{hover.q}</strong>
          {hover.values.map((v, i) => (
            <div key={i}>
              {v.label}: {fmtValue(v.v, unit)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function seriesCSV(series, unit) {
  const quarters = [...new Set(series.flatMap((s) => s.points.map((p) => p.q)))].sort();
  const header = ['quarter', ...series.map((s) => s.label + (unit ? ` (${unit})` : ''))];
  const rows = quarters.map((q) => [q, ...series.map((s) => s.points.find((p) => p.q === q)?.v ?? '')]);
  return { header, rows };
}
