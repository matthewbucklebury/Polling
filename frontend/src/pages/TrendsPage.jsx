import { useEffect, useState } from 'react';
import { get } from '../api.js';
import { useMeta } from '../App.jsx';
import ChartFrame from '../components/ChartFrame.jsx';
import LineChart, { seriesCSV } from '../components/LineChart.jsx';

export default function TrendsPage() {
  const meta = useMeta();
  const [data, setData] = useState(null);
  useEffect(() => {
    get('/api/national').then(setData);
  }, []);
  if (!data) return <div className="sub">Loading…</div>;
  const s4 = data.series_4q;

  const mk = (defs) => defs.filter((d) => (s4[d.m] || []).length).map((d, i) => ({
    key: d.m, label: d.label, points: s4[d.m], colorVar: d.colorVar, dashed: d.dashed,
  }));

  const volume = mk([
    { m: 'received_all', label: 'Applications received', colorVar: '--series-1' },
    { m: 'decisions_all', label: 'Applications decided', colorVar: '--series-2' },
  ]);
  const eot = mk([
    { m: 'eot_share_all', label: 'All decisions', colorVar: '--series-1' },
    { m: 'eot_share_major', label: 'Major decisions', colorVar: '--series-5' },
  ]);
  const speed = mk([
    { m: 'pct_intime_headline_major', label: 'Major — headline (incl. agreements)', colorVar: '--series-1' },
    { m: 'pct_intime_statutory_major', label: 'Major — statutory basis', colorVar: '--series-6' },
    { m: 'pct_intime_headline_minor', label: 'Minor — headline', colorVar: '--series-1', dashed: true },
    { m: 'pct_intime_statutory_minor', label: 'Minor — statutory basis', colorVar: '--series-6', dashed: true },
  ]);
  const approval = mk([
    { m: 'approval_rate_all', label: 'All applications', colorVar: '--series-1' },
    { m: 'approval_rate_major_res', label: 'Major residential', colorVar: '--series-5' },
  ]);
  const appeals = mk([
    { m: 'overturn_rate', label: 'Appeals allowed (share of decided)', colorVar: '--series-1' },
    { m: 'refusal_overturn_rate', label: 'Refusals overturned', colorVar: '--series-5' },
  ]);
  const appealVol = mk([{ m: 'appeals_decided', label: 'Appeals decided', colorVar: '--series-1' }]);
  const netAdd = (data.annual || []).filter((r) => r.metric === 'net_additions');

  return (
    <div>
      <h1>National trends — England</h1>
      <p className="sub">All series are England-wide aggregates of local planning authority data, rolling year (4Q).</p>
      <div className="grid2">
        <ChartFrame
          title="The long decline in decision volumes" subtitle="Applications received and decided, rolling year"
          csv={seriesCSV(volume, 'count')} filename="national-volume"
        >
          <LineChart series={volume} unit="count" />
        </ChartFrame>
        <ChartFrame
          title="The rise of extension-of-time agreements" subtitle="Share of decisions made under a performance agreement / EOT"
          csv={seriesCSV(eot, '%')} filename="national-eot"
        >
          <LineChart series={eot} unit="%" />
        </ChartFrame>
        <ChartFrame
          title="Headline speed vs statutory reality" subtitle="Share of decisions in time: counting agreed extensions vs statutory clock only"
          csv={seriesCSV(speed, '%')} filename="national-speed"
        >
          <LineChart series={speed} unit="%" />
        </ChartFrame>
        <ChartFrame
          title="Approval rates" subtitle="Share of decisions granting permission"
          csv={seriesCSV(approval, '%')} filename="national-approval"
        >
          <LineChart series={approval} unit="%" />
        </ChartFrame>
        <ChartFrame
          title="Appeal outcomes" subtitle="Share of appeals allowed (PINS casework, from 2016)"
          csv={seriesCSV(appeals, '%')} filename="national-appeals"
        >
          <LineChart series={appeals} unit="%" />
        </ChartFrame>
        <ChartFrame
          title="Appeals decided" subtitle="Planning, householder and commercial appeals"
          csv={seriesCSV(appealVol, 'count')} filename="national-appeal-volume"
        >
          <LineChart series={appealVol} unit="count" />
        </ChartFrame>
        {netAdd.length > 0 && (
          <ChartFrame
            title="Net additional dwellings — England" subtitle="Financial years"
            csv={{ header: ['fy_ending', 'net_additions'], rows: netAdd.map((r) => [r.year, r.value]) }}
            filename="national-net-additions"
          >
            <LineChart
              unit="count"
              series={[{ key: 'na', label: 'Net additional dwellings', points: netAdd.map((r) => ({ q: String(r.year), v: r.value })), colorVar: '--series-1' }]}
            />
          </ChartFrame>
        )}
      </div>
    </div>
  );
}
