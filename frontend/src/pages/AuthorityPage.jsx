import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { get, fmtValue } from '../api.js';
import { useMeta } from '../App.jsx';
import ChartFrame from '../components/ChartFrame.jsx';
import LineChart, { seriesCSV } from '../components/LineChart.jsx';

function tri(data, metric, a) {
  // authority (blue) vs region (violet) vs England (muted gray, dashed)
  const s = [];
  const auth = data.series.authority[metric];
  if (auth?.length) s.push({ key: 'a', label: a.name, points: auth, colorVar: '--series-1' });
  const reg = data.series.region?.[metric];
  if (reg?.length) s.push({ key: 'r', label: a.region, points: reg, colorVar: '--series-5' });
  const eng = data.series.england[metric];
  if (eng?.length) s.push({ key: 'e', label: 'England', points: eng, colorVar: '--muted', dashed: true });
  return s;
}

function Chart({ data, a, metric, title, meta }) {
  const info = meta.metrics[metric] || {};
  const series = tri(data, metric, a);
  if (!series.length || !series[0].points.length) return null;
  return (
    <ChartFrame title={title || info.label} subtitle="Rolling year (4Q)" csv={seriesCSV(series, info.unit)} filename={`${a.code}-${metric}`}>
      <LineChart series={series} unit={info.unit} />
    </ChartFrame>
  );
}

export default function AuthorityPage() {
  const { code } = useParams();
  const meta = useMeta();
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    setData(null);
    get(`/api/authorities/${code}`).then(setData).catch((e) => setErr(String(e)));
  }, [code]);

  if (err) return <div className="banner">Failed to load authority: {err}</div>;
  if (!data) return <div className="sub">Loading…</div>;
  const a = data.authority;
  const L = (m) => data.latest[m];

  const friction = L('friction_score');
  const frictionParts = [
    ['friction_approval_rate_major_res', 'Major residential approval', meta.friction.components.approval_rate_major_res?.weight],
    ['friction_pct_intime_statutory_major', 'Statutory-basis speed', meta.friction.components.pct_intime_statutory_major?.weight],
    ['friction_overturn_rate', 'Appeal overturns', meta.friction.components.overturn_rate?.weight],
  ];

  const stats = [
    ['approval_rate_all', 'Approval rate (all)'],
    ['approval_rate_major_res', 'Approval (major residential)'],
    ['pct_intime_headline_major', 'Major in time (headline)'],
    ['pct_intime_statutory_major', 'Major within 13 wks (statutory)'],
    ['eot_share_all', 'Decisions under agreements'],
    ['overturn_rate', 'Appeals overturned'],
  ];

  const hdt = data.annual.filter((r) => r.metric === 'hdt_measure').at(-1);
  const netAdd = data.annual.filter((r) => r.metric === 'net_additions');
  const netAddSeries = [{ key: 'na', label: 'Net additional dwellings', points: netAdd.map((r) => ({ q: String(r.year), v: r.value })), colorVar: '--series-1' }];

  return (
    <div>
      <p className="sub"><Link to="/">← Map</Link></p>
      <h1>{a.name}</h1>
      <p className="sub">
        {a.region} · {(a.authority_type || '').replace('_', ' ')}
        {a.ruc ? ` · ${a.ruc}` : ''}
        {a.population ? ` · population ${a.population.toLocaleString()}` : ''}
        {' · '}
        <a href={`/api/authorities/${a.code}/report`} target="_blank" rel="noreferrer">Download report</a>
      </p>
      <div className="card summaryline">{data.summary}</div>

      <div className="card">
        <h2>Rolling-year snapshot {friction ? `(to ${friction.quarter})` : ''}</h2>
        <div className="statgrid">
          {friction && (
            <div className="stat" style={{ borderColor: 'var(--accent)' }}>
              <div className="v">{friction.value.toFixed(0)}</div>
              <div className="l">Friction score (0 least – 100 most)</div>
              <div className="c">
                {frictionParts.map(([m, label, w]) =>
                  L(m) ? `${label} (w ${w}): ${L(m).value.toFixed(0)}` : `${label}: n/a`
                ).join(' · ')}
              </div>
            </div>
          )}
          {stats.map(([m, label]) => {
            const e = L(m);
            const info = meta.metrics[m] || {};
            return (
              <div className="stat" key={m}>
                <div className="v">{e ? fmtValue(e.value, info.unit) : '–'}</div>
                <div className="l">{label}</div>
              </div>
            );
          })}
          {hdt && (
            <div className="stat">
              <div className="v">{hdt.value.toFixed(0)}%</div>
              <div className="l">Housing Delivery Test {hdt.year}</div>
            </div>
          )}
        </div>
      </div>

      <h2 style={{ margin: '1rem 0 0.5rem' }}>Approvals</h2>
      <div className="grid2">
        <Chart data={data} a={a} metric="approval_rate_major_res" meta={meta} />
        <Chart data={data} a={a} metric="approval_rate_all" meta={meta} />
        <Chart data={data} a={a} metric="approval_rate_minor_res" meta={meta} />
        <Chart data={data} a={a} metric="approval_rate_householder" meta={meta} />
      </div>

      <h2 style={{ margin: '1rem 0 0.5rem' }}>Decision speed and extension agreements</h2>
      <div className="grid2">
        <ChartFrame
          title="Major decisions in time: headline vs statutory basis" subtitle="Rolling year (4Q) — the gap is what extension agreements add"
          csv={seriesCSV(
            [
              { label: 'Headline (incl. agreed extensions)', points: data.series.authority.pct_intime_headline_major || [] },
              { label: 'Within statutory 13 weeks', points: data.series.authority.pct_intime_statutory_major || [] },
            ], '%')}
          filename={`${a.code}-speed-gap`}
        >
          <LineChart
            unit="%"
            series={[
              { key: 'h', label: 'Headline (incl. agreed extensions)', points: data.series.authority.pct_intime_headline_major || [], colorVar: '--series-1' },
              { key: 's', label: 'Within statutory 13 weeks', points: data.series.authority.pct_intime_statutory_major || [], colorVar: '--series-6' },
            ]}
          />
        </ChartFrame>
        <Chart data={data} a={a} metric="eot_share_all" meta={meta} />
        <Chart data={data} a={a} metric="pct_intime_headline_minor" meta={meta} />
        <Chart data={data} a={a} metric="pct_intime_statutory_minor" meta={meta} />
      </div>

      <h2 style={{ margin: '1rem 0 0.5rem' }}>Volume</h2>
      <div className="grid2">
        <ChartFrame
          title="Applications received and decided" subtitle="Rolling year (4Q)"
          csv={seriesCSV(
            [
              { label: 'Received', points: data.series.authority.received_all || [] },
              { label: 'Decided', points: data.series.authority.decisions_all || [] },
            ], 'count')}
          filename={`${a.code}-volume`}
        >
          <LineChart
            unit="count"
            series={[
              { key: 'r', label: 'Received', points: data.series.authority.received_all || [], colorVar: '--series-1' },
              { key: 'd', label: 'Decided', points: data.series.authority.decisions_all || [], colorVar: '--series-2' },
            ]}
          />
        </ChartFrame>
        <Chart data={data} a={a} metric="decisions_vs_5yr" meta={meta} title="Decision volume vs own 5-year average (100 = on trend)" />
      </div>

      <h2 style={{ margin: '1rem 0 0.5rem' }}>Appeals record</h2>
      <div className="grid2">
        <Chart data={data} a={a} metric="overturn_rate" meta={meta} />
        <Chart data={data} a={a} metric="refusal_overturn_rate" meta={meta} />
        <Chart data={data} a={a} metric="appeals_decided" meta={meta} />
        <Chart data={data} a={a} metric="appeal_rate_refusals" meta={meta} />
      </div>

      <h2 style={{ margin: '1rem 0 0.5rem' }}>Housing delivery</h2>
      <div className="grid2">
        {netAdd.length > 0 && (
          <ChartFrame
            title="Net additional dwellings" subtitle="Financial years (year shown = FY ending)"
            csv={{ header: ['fy_ending', 'net_additions'], rows: netAdd.map((r) => [r.year, r.value]) }}
            filename={`${a.code}-net-additions`}
          >
            <LineChart unit="count" series={netAddSeries} />
          </ChartFrame>
        )}
        <div className="card">
          <h2>Housing Delivery Test</h2>
          {hdt ? (
            <>
              <p>
                <strong>{hdt.value.toFixed(0)}%</strong> of homes required over the three years to {hdt.year}
                {' '}({fmtValue(data.annual.find((r) => r.metric === 'hdt_delivered' && r.year === hdt.year)?.value, 'count')} delivered
                vs {fmtValue(data.annual.find((r) => r.metric === 'hdt_required' && r.year === hdt.year)?.value, 'count')} required).
              </p>
              <p className="sub">
                Below 95% requires an action plan; below 85% a 20% buffer; below 75% triggers the presumption in
                favour of sustainable development.
              </p>
            </>
          ) : (
            <p className="sub">No HDT result for this authority (national parks and development corporations are not measured).</p>
          )}
        </div>
      </div>
    </div>
  );
}
