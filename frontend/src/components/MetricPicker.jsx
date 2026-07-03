import { useMeta } from '../App.jsx';

export default function MetricPicker({ value, onChange, id = 'metric' }) {
  const meta = useMeta();
  const groups = {};
  for (const m of meta.rankable) {
    const cat = meta.metrics[m]?.category || 'Other';
    (groups[cat] ||= []).push(m);
  }
  return (
    <label className="ctl" htmlFor={id}>
      Metric
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)}>
        {Object.entries(groups).map(([cat, ms]) => (
          <optgroup key={cat} label={cat}>
            {ms.map((m) => (
              <option key={m} value={m}>
                {meta.metrics[m].label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </label>
  );
}
