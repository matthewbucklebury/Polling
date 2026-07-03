import { useRef } from 'react';
import { downloadCSV, downloadPNG } from '../api.js';

/** Wraps a chart with a title and PNG/CSV export buttons.
 *  csv: { header: [...], rows: [[...], ...] } */
export default function ChartFrame({ title, subtitle, csv, filename, children }) {
  const ref = useRef(null);
  const slug = (filename || title || 'chart').toLowerCase().replace(/[^a-z0-9]+/g, '-');
  return (
    <div className="card chart-frame">
      <div className="exports">
        <button
          title="Download chart as PNG"
          onClick={() => {
            const svg = ref.current?.querySelector('svg');
            if (svg) downloadPNG(svg, `${slug}.png`);
          }}
        >
          PNG
        </button>
        {csv && (
          <button title="Download data as CSV" onClick={() => downloadCSV(`${slug}.csv`, csv.header, csv.rows)}>
            CSV
          </button>
        )}
      </div>
      {title && <h2>{title}</h2>}
      {subtitle && <div className="sub" style={{ marginTop: '-0.4rem', marginBottom: '0.4rem' }}>{subtitle}</div>}
      <div ref={ref}>{children}</div>
    </div>
  );
}
