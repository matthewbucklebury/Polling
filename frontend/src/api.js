const cache = new Map();

export async function get(path) {
  if (cache.has(path)) return cache.get(path);
  const res = await fetch(path);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${path}: ${body.slice(0, 200)}`);
  }
  const data = await res.json();
  cache.set(path, data);
  return data;
}

export function fmtValue(v, unit) {
  if (v == null || Number.isNaN(v)) return '–';
  if (unit === '%') return `${v.toFixed(1)}%`;
  if (unit === 'pp') return `${v.toFixed(1)} pp`;
  if (unit === 'score' || unit === 'index') return v.toFixed(0);
  return Math.round(v).toLocaleString();
}

export function downloadCSV(filename, header, rows) {
  const esc = (c) => {
    const s = String(c ?? '');
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const csv = [header, ...rows].map((r) => r.map(esc).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

// Serialize an <svg> element to PNG. Inline styles are resolved so exports match the screen.
export function downloadPNG(svgEl, filename, scale = 2) {
  const clone = svgEl.cloneNode(true);
  const walk = (src, dst) => {
    const cs = getComputedStyle(src);
    if (src instanceof SVGElement) {
      for (const p of ['fill', 'stroke', 'stroke-width', 'font', 'font-size', 'font-family', 'opacity', 'stroke-dasharray']) {
        const v = cs.getPropertyValue(p);
        if (v) dst.setAttribute(p, v);
      }
    }
    for (let i = 0; i < src.children.length; i++) walk(src.children[i], dst.children[i]);
  };
  walk(svgEl, clone);
  const vb = svgEl.viewBox.baseVal;
  const w = (vb && vb.width) || svgEl.clientWidth, h = (vb && vb.height) || svgEl.clientHeight;
  clone.setAttribute('width', w);
  clone.setAttribute('height', h);
  const bg = getComputedStyle(document.body).backgroundColor;
  const xml = new XMLSerializer().serializeToString(clone);
  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement('canvas');
    canvas.width = w * scale;
    canvas.height = h * scale;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = bg || '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    });
  };
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(xml);
}
