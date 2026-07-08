import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { get } from '../api.js';

/** Search box for the top nav: type a council name, click or press Enter to jump
 *  to its profile. Supports Arrow/Enter/Escape keyboard navigation. */
export default function AuthoritySearch() {
  const nav = useNavigate();
  const [all, setAll] = useState(null);
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const wrapRef = useRef(null);

  useEffect(() => {
    get('/api/authorities').then((d) => setAll(d.authorities));
  }, []);

  const matches = useMemo(() => {
    if (!all || query.trim().length < 2) return [];
    const q = query.trim().toLowerCase();
    return all.filter((a) => a.name.toLowerCase().includes(q)).slice(0, 8);
  }, [all, query]);

  useEffect(() => {
    setHighlight(0);
  }, [query]);

  useEffect(() => {
    const onDocClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  const select = (authority) => {
    if (!authority) return;
    nav(`/authority/${authority.code}`);
    setQuery('');
    setOpen(false);
  };

  const onKeyDown = (e) => {
    if (!open || matches.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, matches.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      select(matches[highlight] || matches[0]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div ref={wrapRef} style={{ position: 'relative', marginLeft: '0.5rem' }}>
      <input
        type="search"
        placeholder="Search a council…"
        aria-label="Search for a local planning authority"
        value={query}
        style={{ width: '100%', maxWidth: 220, minWidth: 120 }}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />
      {open && matches.length > 0 && (
        <div
          className="card"
          style={{ position: 'absolute', top: '100%', left: 0, zIndex: 50, width: 260, padding: '0.3rem', marginTop: 4 }}
        >
          {matches.map((m, i) => (
            <button
              key={m.code}
              onClick={() => select(m)}
              onMouseEnter={() => setHighlight(i)}
              style={{
                border: 'none', width: '100%', textAlign: 'left', display: 'block',
                background: i === highlight ? 'color-mix(in srgb, var(--accent) 12%, transparent)' : 'none',
              }}
            >
              {m.name} <span className="sub">({m.region})</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
