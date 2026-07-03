import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { geoMercator, geoPath } from 'd3-geo';
import { get, fmtValue } from '../api.js';
import { useMeta } from '../App.jsx';
import MetricPicker from '../components/MetricPicker.jsx';
import ChartFrame from '../components/ChartFrame.jsx';

// Sequential single-hue ramps (reference palette blue; red pole of the diverging pair
// for higher-is-bad metrics so "more friction" always reads darker/hotter).
const BLUE = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'];
const RED = ['#fbd9d9', '#f4b0af', '#ec8886', '#e34948', '#c03332', '#992827', '#6f1d1c'];

function ramp(colors, t) {
  const i = Math.max(0, Math.min(colors.length - 1, Math.floor(t * colors.length)));
  return colors[i];
}

export default function MapPage() {
  const meta = useMeta();
  const nav = useNavigate();
  const [metric, setMetric] = useState('friction_score');
  const [qIdx, setQIdx] = useState(meta.quarters.length - 1);
  const [geo, setGeo] = useState(null);
  const [values, setValues] = useState(null);
  const [tip, setTip] = useState(null);
  const wrapRef = useRef(null);
  const quarter = meta.quarters[qIdx];

  useEffect(() => {
    get('/api/geojson').then(setGeo);
  }, []);
  useEffect(() => {
    setValues(null);
    get(`/api/map?metric=${metric}&quarter=${quarter}&window=4Q`).then((d) => setValues(d.values));
  }, [metric, quarter]);

  const info = meta.metrics[metric];
  const colors = info.higher_is === 'bad' ? RED : BLUE;

  const { paths, domain } = useMemo(() => {
    if (!geo) return { paths: null, domain: null };
    const projection = geoMercator().fitSize([560, 640], geo);
    const path = geoPath(projection);
    const feats = geo.features.map((f) => ({ code: f.properties.code, name: f.properties.name, d: path(f) }));
    return { paths: feats, domain: null };
  }, [geo]);

  const [lo, hi] = useMemo(() => {
    if (!values) return [0, 1];
    const vs = Object.values(values).sort((a, b) => a - b);
    if (!vs.length) return [0, 1];
    return [vs[Math.floor(vs.length * 0.02)], vs[Math.ceil(vs.length * 0.98) - 1]];
  }, [values]);

  const color = (code) => {
    const v = values?.[code];
    if (v == null) return 'var(--grid)';
    const t = hi > lo ? (v - lo) / (hi - lo) : 0.5;
    return ramp(colors, Math.max(0, Math.min(0.999, t)));
  };

  const nameOf = useMemo(() => Object.fromEntries((paths || []).map((p) => [p.code, p.name])), [paths]);
  const csv = values
    ? {
        header: ['authority_code', 'authority', 'quarter', metric],
        rows: Object.entries(values).map(([c, v]) => [c, nameOf[c] || '', quarter, v]),
      }
    : null;

  return (
    <div>
      <h1>Local planning authority map</h1>
      <div className="controls">
        <MetricPicker value={metric} onChange={setMetric} />
        <label className="ctl" style={{ flex: '1 1 260px' }}>
          Quarter: rolling year to <strong>{quarter}</strong>
          <input
            type="range" min="0" max={meta.quarters.length - 1} value={qIdx}
            onChange={(e) => setQIdx(+e.target.value)}
          />
        </label>
      </div>
      <div className="map-wrap">
        <ChartFrame title={info.label} subtitle={`Rolling year to ${quarter} · click an authority for its profile`} csv={csv} filename={`map-${metric}-${quarter}`}>
          <div ref={wrapRef} style={{ position: 'relative' }}>
            <svg viewBox="0 0 560 640" className="map-svg" style={{ width: '100%', height: 'auto', display: 'block' }}>
              {paths?.map((p) => (
                <path
                  key={p.code}
                  d={p.d}
                  fill={color(p.code)}
                  style={{ stroke: 'var(--surface)', strokeWidth: 0.4 }}
                  onClick={() => nav(`/authority/${p.code}`)}
                  onMouseMove={(e) => {
                    const r = wrapRef.current.getBoundingClientRect();
                    setTip({
                      x: e.clientX - r.left + 12, y: e.clientY - r.top + 6,
                      name: p.name, v: values?.[p.code],
                    });
                  }}
                  onMouseLeave={() => setTip(null)}
                />
              ))}
            </svg>
            {tip && (
              <div className="chart-tooltip" style={{ left: Math.min(tip.x, 380), top: tip.y }}>
                <strong>{tip.name}</strong>
                <div>{info.label}: {fmtValue(tip.v, info.unit)}</div>
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }} className="sub">
              <span>{fmtValue(lo, info.unit)}</span>
              <div style={{ display: 'flex', height: 10, flex: '0 0 140px', borderRadius: 3, overflow: 'hidden' }}>
                {colors.map((c) => <div key={c} style={{ flex: 1, background: c }} />)}
              </div>
              <span>{fmtValue(hi, info.unit)}</span>
              <span style={{ marginLeft: 8 }}><span className="swatch" style={{ background: 'var(--grid)', display: 'inline-block', width: 10, height: 10, borderRadius: 2 }} /> no data / below threshold</span>
            </div>
          </div>
        </ChartFrame>
        <div className="card">
          <h2>About this metric</h2>
          <p>{info.description}</p>
          <p className="sub">Source: {info.source}</p>
          {info.caveats?.length > 0 && (
            <p className="sub">⚠ {info.caveats[0]}</p>
          )}
          <p className="sub">
            National parks and development corporations are planning authorities too but have no LAD boundary, so they
            don't appear on the map — find them via League tables.
          </p>
        </div>
      </div>
    </div>
  );
}
