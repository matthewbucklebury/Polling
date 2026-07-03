import { useEffect, useMemo, useState } from 'react';
import { get } from '../api.js';
import { useMeta } from '../App.jsx';
import MetricPicker from '../components/MetricPicker.jsx';
import ChartFrame from '../components/ChartFrame.jsx';
import LineChart, { seriesCSV } from '../components/LineChart.jsx';

const SLOTS = ['--series-1', '--series-2', '--series-3', '--series-5', '--series-6'];

export default function ComparePage() {
  const meta = useMeta();
  const [all, setAll] = useState(null);
  const [codes, setCodes] = useState([]);
  const [metric, setMetric] = useState('approval_rate_major_res');
  const [query, setQuery] = useState('');
  const [data, setData] = useState(null);

  useEffect(() => {
    get('/api/authorities').then((d) => setAll(d.authorities));
  }, []);
  useEffect(() => {
    if (!codes.length) return setData(null);
    get(`/api/compare?codes=${codes.join(',')}&metric=${metric}`).then(setData);
  }, [codes, metric]);

  const matches = useMemo(() => {
    if (!all || query.length < 2) return [];
    const q = query.toLowerCase();
    return all.filter((a) => a.name.toLowerCase().includes(q) && !codes.includes(a.code)).slice(0, 8);
  }, [all, query, codes]);

  const info = meta.metrics[metric];
  const series = data
    ? [
        ...codes
          .map((c, i) => ({
            key: c,
            label: data.names[c] || c,
            points: data.series[c] || [],
            colorVar: SLOTS[i % SLOTS.length],
          }))
          .filter((s) => s.points.length),
        { key: 'ENG', label: 'England', points: data.series.ENG || [], colorVar: '--muted', dashed: true },
      ]
    : [];

  return (
    <div>
      <h1>Compare authorities</h1>
      <div className="controls">
        <MetricPicker value={metric} onChange={setMetric} />
        <label className="ctl" style={{ position: 'relative' }}>
          Add authority (up to 5)
          <input
            type="search" placeholder="Type a name…" value={query}
            onChange={(e) => setQuery(e.target.value)} style={{ width: 220 }}
          />
          {matches.length > 0 && (
            <div className="card" style={{ position: 'absolute', top: '100%', left: 0, zIndex: 40, width: 260, padding: '0.3rem' }}>
              {matches.map((m) => (
                <div key={m.code}>
                  <button
                    style={{ border: 'none', width: '100%', textAlign: 'left' }}
                    onClick={() => {
                      if (codes.length < 5) setCodes([...codes, m.code]);
                      setQuery('');
                    }}
                  >
                    {m.name} <span className="sub">({m.region})</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </label>
      </div>
      <div className="chips" style={{ marginBottom: '0.8rem' }}>
        {codes.map((c, i) => (
          <span className="chip" key={c} style={{ background: `color-mix(in srgb, var(${SLOTS[i % SLOTS.length]}) 15%, transparent)`, color: `var(${SLOTS[i % SLOTS.length]})` }}>
            {data?.names?.[c] || all?.find((a) => a.code === c)?.name || c}
            <button onClick={() => setCodes(codes.filter((x) => x !== c))} aria-label="remove">×</button>
          </span>
        ))}
        {!codes.length && <span className="sub">Pick authorities to overlay their series. England is always shown for reference.</span>}
      </div>
      {data && series.length > 0 && (
        <ChartFrame title={info.label} subtitle="Rolling year (4Q)" csv={seriesCSV(series, info.unit)} filename={`compare-${metric}`}>
          <LineChart series={series} unit={info.unit} height={320} />
        </ChartFrame>
      )}
    </div>
  );
}
