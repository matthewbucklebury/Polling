import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { get, fmtValue, downloadCSV } from '../api.js';
import { useMeta } from '../App.jsx';
import MetricPicker from '../components/MetricPicker.jsx';

export default function LeaguePage() {
  const meta = useMeta();
  const [metric, setMetric] = useState('friction_score');
  const [quarter, setQuarter] = useState(meta.latest_quarter);
  const [region, setRegion] = useState('');
  const [atype, setAtype] = useState('');
  const [ruc, setRuc] = useState('');
  const [minDen, setMinDen] = useState('');
  const [asc, setAsc] = useState(false);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    const p = new URLSearchParams({ metric, quarter, window: '4Q' });
    if (region) p.set('region', region);
    if (atype) p.set('authority_type', atype);
    if (ruc) p.set('ruc', ruc);
    if (minDen !== '') p.set('min_denominator', minDen);
    setData(null);
    get(`/api/league?${p}`).then(setData).catch((e) => setErr(String(e)));
  }, [metric, quarter, region, atype, ruc, minDen]);

  const info = meta.metrics[metric];
  if (err) return <div className="banner">{err}</div>;

  const entries = data ? (asc ? [...data.entries].reverse() : data.entries) : [];
  const rucShort = (r) => (r || '').split(':')[0];

  return (
    <div>
      <h1>League tables</h1>
      <div className="controls">
        <MetricPicker value={metric} onChange={setMetric} />
        <label className="ctl">
          Rolling year to
          <select value={quarter} onChange={(e) => setQuarter(e.target.value)}>
            {[...meta.quarters].reverse().map((q) => <option key={q}>{q}</option>)}
          </select>
        </label>
        <label className="ctl">
          Region
          <select value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="">All regions</option>
            {meta.regions.map((r) => <option key={r}>{r}</option>)}
          </select>
        </label>
        <label className="ctl">
          Authority type
          <select value={atype} onChange={(e) => setAtype(e.target.value)}>
            <option value="">All types</option>
            {meta.authority_types.map((t) => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
          </select>
        </label>
        <label className="ctl">
          Rural / urban
          <select value={ruc} onChange={(e) => setRuc(e.target.value)}>
            <option value="">All classes</option>
            {[...new Set(meta.rucs.map(rucShort))].map((r) => <option key={r}>{r}</option>)}
          </select>
        </label>
        {data?.denominator_metric && (
          <label className="ctl">
            Min {meta.metrics[data.denominator_metric]?.label?.toLowerCase() || 'denominator'} (4Q)
            <input
              type="number" min="0" style={{ width: 90 }} value={minDen === '' ? data.min_denominator ?? 0 : minDen}
              onChange={(e) => setMinDen(e.target.value)}
            />
          </label>
        )}
        <button
          onClick={() =>
            data &&
            downloadCSV(`league-${metric}-${quarter}.csv`,
              ['rank', 'authority', 'code', 'region', 'type', 'ruc', metric, data.denominator_metric || 'denominator'],
              entries.map((e) => [e.rank, e.name, e.code, e.region, e.authority_type, e.ruc, e.value, e.denominator ?? '']))
          }
        >
          CSV
        </button>
      </div>

      {!data ? (
        <div className="sub">Loading…</div>
      ) : (
        <div className="card">
          <p className="sub">
            {info.description} {info.higher_is === 'bad' ? 'Ranked best (lowest) first.' : info.higher_is === 'good' ? 'Ranked best (highest) first.' : 'Ranked highest first.'}
            {data.min_denominator ? ` Authorities with fewer than ${data.min_denominator} ${meta.metrics[data.denominator_metric]?.label?.toLowerCase() || ''} in the window are excluded (${data.excluded_below_threshold} hidden).` : ''}
            {data.england != null && <> England: <strong>{fmtValue(data.england, info.unit)}</strong>.</>}
          </p>
          <div style={{ overflowX: 'auto' }}>
            <table className="data">
              <thead>
                <tr>
                  <th className="num" onClick={() => setAsc(!asc)}>Rank {asc ? '↑' : '↓'}</th>
                  <th>Authority</th>
                  <th>Region</th>
                  <th>Type</th>
                  <th>Rural/urban</th>
                  <th className="num">{info.label}</th>
                  {data.denominator_metric && <th className="num">{meta.metrics[data.denominator_metric]?.label}</th>}
                </tr>
              </thead>
              <tbody>
                {entries.map((e) => (
                  <tr key={e.code}>
                    <td className="num">{e.rank}</td>
                    <td><Link to={`/authority/${e.code}`}>{e.name}</Link></td>
                    <td>{e.region}</td>
                    <td>{(e.authority_type || '').replace('_', ' ')}</td>
                    <td>{rucShort(e.ruc)}</td>
                    <td className="num"><strong>{fmtValue(e.value, info.unit)}</strong></td>
                    {data.denominator_metric && <td className="num">{e.denominator != null ? Math.round(e.denominator).toLocaleString() : '–'}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
