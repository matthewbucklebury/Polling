# Task 05 — Shareable URLs for map and compare views

**Priority: COULD · Model: Sonnet · Depends on: Task 00.**

## Objective

The map page always opens on friction score / latest quarter, and the compare page
always opens empty. Encode their state in the URL (`/?metric=…&quarter=…` and
`/compare?codes=…&metric=…`) so views can be bookmarked, shared, and survive refresh.

## Files involved

- `frontend/src/pages/MapPage.jsx` and `frontend/src/pages/ComparePage.jsx` only.
- Use `useSearchParams` from `react-router-dom` (already a dependency).

## Approach

1. MapPage: initialise `metric` and `qIdx` from search params when present and valid
   (metric must be in `meta.rankable`; quarter must be in `meta.quarters` — fall back to
   defaults silently otherwise). Update the params (replace, not push — no history spam)
   whenever either changes.
2. ComparePage: same for `codes` (comma-separated, cap 5, drop codes not in the
   authorities list) and `metric`.
3. `make build`, `node scripts/check_app.mjs`, `make test`.

## Acceptance criteria

- `http://127.0.0.1:8000/?metric=overturn_rate&quarter=2024Q4` opens the map already on
  that metric/quarter.
- `http://127.0.0.1:8000/compare?codes=E07000223,E06000063&metric=approval_rate_all`
  opens the comparison pre-loaded.
- Invalid params fall back to defaults without errors (test `?metric=garbage`).
- Browser Back button does not step through every slider tick (params replaced).

## How Matt verifies this

1. On the map, pick metric "Appeals overturn rate" and drag the slider back a few years.
2. Copy the address bar URL, open a NEW browser tab, paste it — the map opens exactly as
   you left it (same metric, same quarter shown above the slider).
3. On Compare, add two councils, copy the URL, open in a new tab — the same comparison
   loads.
4. Edit the address bar to end `?metric=nonsense` and press Enter — the page loads
   normally on the default view (no error screen).

## Do not

- Do not add state to League/Trends pages in this task (scope creep).
- Do not change API endpoints — this is purely frontend URL state.

## Rollback

`git checkout -- frontend/src/pages/MapPage.jsx frontend/src/pages/ComparePage.jsx && make build`.
