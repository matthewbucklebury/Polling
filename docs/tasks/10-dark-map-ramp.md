# Task 10 — Dark-mode map ramp tuning

**Priority: COULD · Model: Sonnet · Depends on: Task 00.**

## Objective

The choropleth's colour ramps (`BLUE`, `RED` in `frontend/src/pages/MapPage.jsx`) were
selected for the light surface. On dark mode they work but the lightest steps glow
brighter than intended and the ramp isn't a validated dark-mode scale. Select proper
dark-mode ramps and switch on `prefers-color-scheme`.

## Files involved

- `frontend/src/pages/MapPage.jsx` — the two ramp arrays and the `color()` function.

## Approach

1. Read the dataviz palette reference (`docs/` has no copy — the ramps follow the
   sequential-scale rule: one hue, light→dark on light surfaces; on dark surfaces the
   scale runs dark→light so "more" still reads as "more ink/intensity"). Derive a
   7-step dark-mode blue from the existing light ramp reversed and darkened at the low
   end (lowest step must stay distinguishable from the `--grid` no-data grey), and a
   matching dark red.
2. Detect mode with `window.matchMedia('(prefers-color-scheme: dark)')` (and listen for
   changes) or, simpler and acceptable: read a CSS custom property set per-mode in
   `styles.css` (e.g. define `--ramp-blue-1..7` in both `:root` blocks and build the JS
   array from `getComputedStyle`). Choose one; keep it small.
3. Keep the legend gradient and "no data" grey working in both modes.
4. `make build`, `node scripts/check_app.mjs` (it screenshots dark mode — LOOK at
   `scripts/screenshots/map-dark.png`), `make test`.

## Acceptance criteria

- In dark mode: map readable, high values clearly "hotter/darker-inked" than low, no-data
  authorities clearly distinct from low values, legend matches the fills.
- Light mode pixel-identical in intent (same ramps as today).
- check_app passes; the dark screenshot is actually inspected, not just generated.

## How Matt verifies this

1. Put your Mac in dark mode (System Settings → Appearance → Dark).
2. Open the map: it should look deliberately designed — dark background, colours that
   step evenly from faint to strong. Grey "no data" areas must not look like the faint
   end of the scale.
3. Switch back to Light appearance and reload — the map looks exactly as it always did.

## Do not

- Do not touch chart line colours or `styles.css` series tokens (they were selected for
  both modes already) — this task is the MAP ramps only.

## Rollback

`git checkout -- frontend/src/pages/MapPage.jsx frontend/src/styles.css && make build`.
