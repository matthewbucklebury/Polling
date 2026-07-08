import { createContext, useContext, useEffect, useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';
import { get } from './api.js';
import MapPage from './pages/MapPage.jsx';
import AuthorityPage from './pages/AuthorityPage.jsx';
import LeaguePage from './pages/LeaguePage.jsx';
import ComparePage from './pages/ComparePage.jsx';
import TrendsPage from './pages/TrendsPage.jsx';
import DictionaryPage from './pages/DictionaryPage.jsx';
import AuthoritySearch from './components/AuthoritySearch.jsx';

const MetaContext = createContext(null);
export const useMeta = () => useContext(MetaContext);

export default function App() {
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    get('/api/meta').then(setMeta).catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="page">
        <h1>UK Planning Tracker</h1>
        <div className="banner">Could not reach the API: {error}. Is the database built? Run <span className="mono">make pipeline</span>.</div>
      </div>
    );
  }
  if (!meta) return <div className="page sub">Loading…</div>;

  const nav = [
    ['/', 'Map', true],
    ['/league', 'League tables'],
    ['/compare', 'Compare'],
    ['/trends', 'National trends'],
    ['/dictionary', 'Data dictionary'],
  ];
  return (
    <MetaContext.Provider value={meta}>
      <nav className="topnav">
        <span className="brand">🏗️ UK Planning Tracker</span>
        {nav.map(([to, label, end]) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => 'nav' + (isActive ? ' active' : '')}>
            {label}
          </NavLink>
        ))}
        <span style={{ marginLeft: 'auto' }}>
          <AuthoritySearch />
        </span>
        <span className="sub">England · data to {meta.latest_quarter}</span>
      </nav>
      <div className="page">
        {meta.sample_sources.length > 0 && (
          <div className="banner">
            ⚠️ Synthetic sample data is standing in for: <strong>{meta.sample_sources.join(', ')}</strong> (source
            download failed — see PIPELINE_STATUS.md). Everything else is real.
          </div>
        )}
        <Routes>
          <Route path="/" element={<MapPage />} />
          <Route path="/authority/:code" element={<AuthorityPage />} />
          <Route path="/league" element={<LeaguePage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/trends" element={<TrendsPage />} />
          <Route path="/dictionary" element={<DictionaryPage />} />
        </Routes>
        <p className="footerline">
          Sources: MHCLG planning application statistics · Planning Inspectorate casework · MHCLG live tables 122 &
          Housing Delivery Test · ONS Open Geography. Local project — not an official publication.
        </p>
      </div>
    </MetaContext.Provider>
  );
}
