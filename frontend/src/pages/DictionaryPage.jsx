import { useMeta } from '../App.jsx';

function Entry({ id, m }) {
  return (
    <div style={{ marginBottom: '0.9rem' }}>
      <strong>{m.label}</strong> <span className="mono sub">({id})</span>
      <div>{m.description}</div>
      <div className="sub">Source: {m.source} · unit: {m.unit} · {m.higher_is === 'neutral' ? 'no good/bad direction' : `higher is ${m.higher_is}`}</div>
      {(m.caveats || []).map((c, i) => (
        <div className="caveat" key={i}>⚠ {c}</div>
      ))}
    </div>
  );
}

export default function DictionaryPage() {
  const meta = useMeta();
  const cats = {};
  for (const [id, m] of Object.entries(meta.metrics)) (cats[m.category] ||= []).push([id, m]);
  for (const [id, m] of Object.entries(meta.annual_metrics)) (cats[m.category] ||= []).push([id, m]);

  return (
    <div className="dict">
      <h1>Data dictionary</h1>
      <div className="card">
        <h2>How to read this data</h2>
        <p>
          Quarterly figures are noisy; every headline view uses a <strong>rolling year (4Q)</strong> — the trailing four
          quarters summed before any rate is computed. Quarters are labelled by calendar quarter as published
          (2024Q2 = April–June 2024). Delivery data is by financial year (the year shown is the FY end).
        </p>
        <p>
          <strong>Known distortions to keep in mind everywhere:</strong>
        </p>
        <ul>
          <li>
            <strong>Extension-of-time agreements.</strong> The government's headline "% in time" counts a decision as
            in time if it met an <em>agreed extended</em> deadline. Around 40% of decisions are now made under such
            agreements (single digits in 2013), so headline speed is not comparable over time. This app always shows
            the statutory-basis measure alongside.
          </li>
          <li>
            <strong>COVID-era anomalies (2020Q2–2021Q4).</strong> Volumes collapsed then surged; speed and appeal
            timelines were disrupted. Treat that period as a break, not a trend.
          </li>
          <li>
            <strong>Local government reorganisation.</strong> 2009, 2019, 2020, 2021 and 2023 mergers are handled by
            summing predecessor districts into successor authorities, so series are continuous — but a "North
            Yorkshire" value from 2015 describes seven former districts. Pre-2009 legacy authorities that cannot be
            mapped are excluded from rankings. See <span className="mono">data/reference/authority_changes.csv</span>.
          </li>
          <li>
            <strong>Small denominators.</strong> Many authorities decide fewer than a dozen major residential schemes
            a year. League tables apply minimum-volume thresholds by default; the map shows values wherever they
            exist, so check volumes on the authority profile before drawing conclusions.
          </li>
          <li>
            <strong>Appeal timing.</strong> An appeal decided this quarter concerns a refusal from several quarters
            ago, so appeal rates computed against same-period refusals are indicative only.
          </li>
          <li>
            <strong>County matters are excluded.</strong> Minerals and waste applications decided by county councils
            (CPS1/CPS2 returns) are out of scope; volumes are small but non-zero.
          </li>
        </ul>
      </div>
      {Object.entries(cats).map(([cat, entries]) => (
        <div className="card" key={cat}>
          <h2>{cat}</h2>
          {entries.map(([id, m]) => (
            <Entry key={id} id={id} m={m} />
          ))}
        </div>
      ))}
      <div className="card">
        <h2>Friction score weighting</h2>
        <p>
          Configured in <span className="mono">config/settings.yml</span> (edit and rerun the pipeline to change):
        </p>
        <ul>
          {Object.entries(meta.friction.components).map(([m, c]) => (
            <li key={m}>
              <strong>{c.label}</strong> — weight {c.weight}, {c.direction === 'inverse' ? 'lower value ⇒ more friction' : 'higher value ⇒ more friction'}
              {c.min_denominator ? `, needs ≥ ${c.min_denominator} in the 4Q window` : ''}
            </li>
          ))}
        </ul>
        <p className="sub">
          Each component is a percentile rank (0–100) across active English authorities in the same quarter; the
          composite is the weighted mean of available components (weights renormalise when a component is missing).
        </p>
      </div>
    </div>
  );
}
