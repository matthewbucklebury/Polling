# Task 02 — Authority search box in the top bar

**Priority: SHOULD · Model: Sonnet · Depends on: Task 00.**

## Objective

Right now the only ways to reach a council's profile are clicking the map or a league
table row. Add a search box to the top navigation bar that jumps straight to any
authority's profile. This is the single biggest usability gap.

## Files involved

- `frontend/src/App.jsx` — the top nav lives here; add the search component to it.
- New file `frontend/src/components/AuthoritySearch.jsx`.
- `frontend/src/styles.css` — reuse existing tokens/classes; the Compare page's
  suggestion dropdown (`frontend/src/pages/ComparePage.jsx`) already implements the same
  pattern — copy its approach (fetch `/api/authorities` via `get()`, filter client-side
  on `name.toLowerCase().includes(query)` from 2 characters, show top 8).

## Approach

1. Build `AuthoritySearch.jsx`: an `<input type="search">` with a dropdown of matches;
   selecting one calls `useNavigate()` to `/authority/{code}` and clears the input.
   Support keyboard: ArrowDown/ArrowUp to move a highlight, Enter to select the
   highlighted (or first) match, Escape to close.
2. Mount it in the top nav in `App.jsx`, before the "England · data to …" label. On
   small screens it should shrink but stay usable (test at 375px width).
3. `make build`, `make run`, then run `node scripts/check_app.mjs` (app running) —
   must pass with no JS errors.
4. `make test` (nothing backend changed, but always run it).

## Acceptance criteria

- Typing "cumb" in the top bar shows "Cumberland"; clicking or pressing Enter opens
  Cumberland's profile from ANY page (map, league, trends…).
- Works with keyboard only. Dropdown closes on Escape and when clicking elsewhere.
- `scripts/check_app.mjs` passes; layout not broken at 375px (screenshot both).

## How Matt verifies this

1. Open http://127.0.0.1:8000 and look at the top bar — there is a search box.
2. Type `oxf` — a small list appears including "Oxford". Click it — the Oxford profile
   opens.
3. From the National trends page, type `cumb` and press Enter — Cumberland's profile
   opens.
4. Make the browser window very narrow (drag the edge) — the search box is still there
   and usable, nothing overlaps.

## Do not

- Do not add a search library or any new npm dependency — plain React like ComparePage.
- Do not touch backend files; `/api/authorities` already returns everything needed.
- Do not restyle the nav beyond adding the box.

## Rollback

`git checkout -- frontend/src/App.jsx frontend/src/styles.css && git clean -f frontend/src/components/AuthoritySearch.jsx && make build`.
