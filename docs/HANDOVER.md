# HANDOVER — UK Planning Applications Tracker

**Last updated: 2026-07-03 (Claude Sonnet 5 session — Task 02 complete)**

This is the master document for continuing work. Read it at the start of every session,
update it at the end of every session (see the session-close protocol in `CLAUDE.md`).

---

## 1. What this project is (for Matt)

A private website that runs on your MacBook and answers questions like: *which councils
approve the fewest housing schemes? which are slowest? which keep losing appeals? which
are missing their housing targets?* — using the government's own published statistics.
It has a colour-coded map of England, a profile page for every council, sortable league
tables, a comparison tool, national trend charts, and a page explaining every number and
its caveats. New government data comes out quarterly; a "pipeline" command refreshes
everything. It is built so it could become a public website later, but nothing is
published anywhere today.

## 2. Current state — honest three buckets

### Works and verified (as of 2026-07-03)

- **Full pipeline from a clean slate**: all four sources downloaded live and loaded —
  MHCLG PS1/PS2 (3.43M fact rows, 1979→2026Q1), PINS appeals casework (149k decided
  appeals 2016→, 94k fact rows), Live Table 122 + HDT 2023 (8.9k values), ONS boundaries
  + rural/urban class (296 features) + NOMIS population (289 authorities matched).
- **Derived metrics**: 3.98M rows — approval rates, headline vs statutory speed, EOT
  share/gap, appeal overturn rates, volume trends, friction score with components,
  England + region aggregates. Spot-checked against known national figures (England
  approval ~87%, EOT share ~40%, appeal allow rate ~30–32%, net additions 221k in
  2023-24 — all match published numbers).
- **Every app page renders** in light *and* dark mode, desktop *and* 375px mobile, with
  zero JavaScript errors (checked with headless Chromium; screenshots reviewed).
- **All 33 automated tests pass** (`make test`): parser fixtures, reorganisation-chain
  mapping, rolling/ratio derivation maths, API smoke tests.
- **Exports**: PNG + CSV per chart, league CSV, per-authority self-contained HTML report.
- **Authority search box** in the top nav (Task 02, 2026-07-03): type ≥2 characters,
  see up to 8 matches, click or Arrow+Enter to jump straight to that council's profile
  from any page. Works with mouse and keyboard, closes on Escape/click-away, verified
  at 375px width (own row, full width, nothing overlaps).
- Reorganisation mapping (2009–2023 mergers, legacy pre-2009 codes by name), sample-data
  fallback with UI banner, PIPELINE_STATUS.md generation.

### Probably works, unverified

- **`make setup` on a fresh macOS machine.** Everything was built and tested on Linux.
  The stack is standard (Python 3.11+, Node 18+) and nothing is platform-specific, but
  no one has run it on the actual MacBook Air yet. First thing to do tomorrow (Task 00).
- **PNG chart export in Safari** (verified in Chromium only; SVG-to-canvas export can
  behave differently in Safari — if broken there, use Chrome, or fix under a small task).
- The pipeline's behaviour when gov.uk URLs *actually* die (the skip-and-continue path
  is unit-tested and the sample-data fallback code-reviewed, but a real dead-link
  overnight has never happened yet).

### Known broken / unfinished

- Nothing known broken. Deliberate exclusions (not bugs): county-matters minerals &
  waste returns, Wales/Scotland, pre-2009 legacy authorities that can't be mapped
  (excluded from rankings), national parks/development corporations not on the map (no
  LAD boundary — they are in league tables). Only the 2023 HDT measurement is loaded
  (earlier years are Task 03).

## 3. How it all fits together (change-impact map)

```
config/sources.yml ──► pipeline/sources/*.py ──► facts / annual / boundaries / authorities
   (URLs change              (fetch+parse+load,          (SQLite, data/planning.sqlite)
    quarterly)                fail loudly per file)               │
config/settings.yml ──► pipeline/metrics.py ────────────► metrics table (4M rows)
   (friction weights,        (canonical authorities,              │
    thresholds)               rolling 4Q sums, ratios,            ▼
                              friction percentiles)      backend/api.py  ◄── backend/catalog.py
                                                          (read-only)        (metric labels, units,
docs in-app  ◄────────────────────────────────────────────────┘               caveats, thresholds)
frontend/src/* ──(npm run build)──► frontend/dist/ ──served by── backend/main.py
```

Ripple rules:

- **Change a source URL** → only `config/sources.yml` (+ delete the stale file in
  `data/raw/`). Nothing else.
- **Add/rename a metric** → `pipeline/metrics.py` (derivation) **and**
  `backend/catalog.py` (label/unit/direction/caveats/threshold) must change together;
  frontend pickers and the dictionary read the catalogue via `/api/meta`, so they update
  themselves. Rerun `make pipeline-offline` to repopulate metrics.
- **Change friction weights/thresholds** → `config/settings.yml`, then
  `make pipeline-offline` (metrics are precomputed, not live).
- **Frontend change** → `make build` before `make run` shows it (the Makefile rebuilds
  automatically when files under `frontend/src/` change).
- **Schema change** → touches `pipeline/db.py` + every loader + likely `backend/api.py`;
  needs a full `make pipeline` rebuild. Avoid without an explicit task.
- The **authorities table** is seeded by boundaries (`authority_meta`) and enriched by
  the MHCLG source (names/regions/types); PINS only adds authorities it can't find.
  Order matters and is fixed in `pipeline/cli.py` (`ORDER`).

## 4. Milestones

| Milestone | Status |
|---|---|
| M1 — Working tracker on real data, all pages, tests, docs | ✅ done (this session) |
| M2 — Runs on Matt's MacBook; Matt can operate it alone | ⬜ Task 00, 01 |
| M3 — Hardened & polished (search, HDT history, print/report polish) | 🟨 Task 02 ✅; 03, 05, 06, 10 pending |
| M4 — Deeper analytics (appeal timeliness, targets, county matters) | ⬜ Tasks 04, 09, 11 |
| M5 — Expansion (Wales scoping, DB slimming, hosting) | ⬜ Tasks 07, 08 (scoping only) |

## 5. Task backlog (ordered; briefs in docs/tasks/)

| # | Task | Priority | Model | Depends on |
|---|---|---|---|---|
| 00 | [First run on Matt's MacBook](tasks/00-first-run-on-mac.md) | MUST | Sonnet | — (still outstanding — see note below) |
| 01 | [Quarterly data refresh drill](tasks/01-refresh-drill.md) | MUST | Sonnet | 00 |
| 02 | ~~[Authority search box in the top bar](tasks/02-authority-search.md)~~ | SHOULD | Sonnet | ✅ **done 2026-07-03** |
| 03 | [Load HDT history 2018–2022](tasks/03-hdt-history.md) | SHOULD | Sonnet | 00 |
| 04 | [Appeal decision-speed metric](tasks/04-appeal-timeliness-metric.md) | SHOULD | **Opus** | 00 |
| 05 | [Shareable URLs for map & compare](tasks/05-shareable-urls.md) | COULD | Sonnet | 00 |
| 06 | [Report & print polish](tasks/06-report-print-polish.md) | COULD | Sonnet | 00 |
| 07 | [Slim the 1.2 GB database](tasks/07-db-slim.md) | COULD | **Opus** | 00 |
| 08 | [Wales scoping study (research, no code)](tasks/08-wales-scoping.md) | COULD | **Opus** | — |
| 09 | [County matters (minerals & waste)](tasks/09-county-matters.md) | COULD | **Opus** | 01 |
| 10 | [Dark-mode map ramp tuning](tasks/10-dark-map-ramp.md) | COULD | Sonnet | 00 |
| 11 | [Housing targets vs delivery](tasks/11-housing-targets.md) | COULD | **Opus** | 03 |

If the four weeks run short: do 00 and 01, then whatever of 02/03 appeals — everything
else is optional polish on an already-complete v1.

**Note on Task 00**: this session (2026-07-03, Sonnet) ran in the same cloud
environment as the original build, NOT on Matt's actual MacBook Air. Task 02 was
completed and verified here, but Task 00 (first run on the real Mac) is still
genuinely outstanding — it needs a session where Claude Code is actually running via
Terminal on that physical machine. Don't assume it's done because other tasks have
been.

## 6. Risk register

| Risk | What Matt sees | First thing to try |
|---|---|---|
| gov.uk changes asset URLs at the next quarterly release (certain, ~every quarter) | `make pipeline` output contains `FAILED` and `PIPELINE_STATUS.md` shows ❌ for a source; app still runs on old data | Follow the `quarterly-data-refresh` skill: open the landing page listed in `config/sources.yml`, copy the new file URL in, delete the old file from `data/raw/`, rerun |
| MHCLG renames PS2 columns (rare) | Pipeline fails with "expected PS2 columns missing, e.g. […]" | The error names the missing columns; update `_ps2_wanted_columns()` in `pipeline/sources/mhclg_applications.py` to the new names; fixtures/tests then need the same rename |
| Stale cache after URL update | Pipeline "succeeds" instantly but data doesn't change; log says "using cached …" | Delete the relevant file(s) in `data/raw/` and rerun — the cache is by filename, this is rule 6 in CLAUDE.md |
| PINS changes workbook sheet names | Pipeline fails naming the file and sheet | Update `sheet:` in `config/sources.yml` to match the new sheet name (open the xlsx to look) |
| HDT resumes publication under new NPPF rules with a new format | Task 03/11 parsers fail on the new file | Treat as a new file: inspect layout first, extend `parse_hdt` carefully, keep old files working |
| Metrics look wrong after touching `pipeline/metrics.py` | Numbers on profiles/league change wildly; England approval rate should always be ~85–90% recent years | `git diff` that file; revert unless the change was the task; the derivation tests in `tests/test_metrics.py` encode the expected maths |
| Absurd-looking values that are real | e.g. Oxford HDT 2023 = 1451% | Not a bug: Oxford's 3-year requirement was 125 homes (collapsed household projections), delivery 1,814. Verified against the raw ODS. Leave it |
| 2026Q2 (or any trailing quarter) looks sparse | Map mostly grey on latest quarter for some metric | Appeals data runs a quarter ahead of MHCLG data; the UI quarter list is capped at MHCLG coverage on purpose (`/api/meta`) |
| DB file ballooning worries | `data/planning.sqlite` is ~1.2 GB | By design (8M rows + indexes). Only Task 07 may change this |
| Safari PNG export fails | Clicking PNG does nothing / blank image in Safari | Use Chrome; or a small task to swap the export to a canvas-based rasteriser |
| Frontend edits invisible | Change made but app looks the same | `make build` didn't run or browser cache: run `make run` again, hard-refresh (Cmd+Shift+R) |

**Fragile, do-not-touch-outside-their-task:** `pipeline/metrics.py`,
`pipeline/sources/mhclg_applications.py` column map, `data/reference/authority_changes.csv`,
metric ids in `backend/catalog.py`, the `.gitignore` data rules (WAL/SHM files must stay
ignored or `git add` fails mid-pipeline with "unstable object source data").

## 7. Decision log (do not relitigate without new information)

| Decision | Why |
|---|---|
| PS1/PS2 **open-data CSVs** over the classic ODS live tables | Same numbers, machine-friendly, one row per LPA-quarter, no merged headers |
| Quarters stored as calendar `YYYYQn` exactly as published | Matches source labels; lexically sortable; FY-vs-CQ confusion documented in dictionary instead of re-labelled |
| Rolling-annual ratios = **sum of counts over 4Q, then divide** | Mean-of-ratios is wrong for small denominators; tested in `tests/test_metrics.py` |
| Reorganisation: predecessors **summed into successors** for all history | Counts are additive; gives continuous series; documented as a caveat rather than breaking series |
| Speed measured **both ways** (headline incl. agreed extensions, and statutory-basis) with the gap and agreement share as first-class metrics | The whole point of the app: EOT agreements flatter headline numbers; PS2's "excluding PAs / PAs only" split supports it directly |
| Friction score = weighted **percentile ranks**, weights in `config/settings.yml`, components always displayed | Transparent, configurable, no fake precision; relative by construction (median = 50) |
| Appeals: only Planning / Householder (HAS) / Commercial (CAS) casework; Allowed+`Allowed with Conditions` = allowed; `Split Decision` = split | These are the appeal types a refused applicant lodges; enforcement etc. would distort overturn rates |
| County matters (CPS1/2) excluded | Tiny volumes; would double-count against district totals; revisit = Task 09 |
| England aggregates computed from LPA rows and verified to equal the published England row (LT122: exact match) | Trust check on the whole load path |
| Charts hand-rolled SVG (no chart library) | Full control of PNG export + palette tokens; one `LineChart` reused everywhere |
| Boundaries: `LAD_MAY_2024_EW_BUC_RUC` single ArcGIS query | Boundaries + rural/urban classification in one 0.6 MB fetch |
| Population from NOMIS `TYPE434` geography | The only NOMIS geography type matching post-2023 LADs (TYPE423 matched just 153/296) |
| Sample data only when a dataset is completely empty, tagged and bannered | App must always boot; fake data must be unmistakable |
| DB size 1.2 GB accepted | Local-first on a modern laptop; slimming is speculative optimisation (Task 07 if it ever matters) |

## 8. Session log

*(Newest first. Every session appends an entry: date, model, what was done, what was
verified, recommended next step.)*

- **2026-07-03 · Claude Sonnet 5 (Task 02).** Confirmed via user Q&A that this session
  is a cloud environment, not Matt's actual MacBook — Task 00 remains outstanding (see
  note in section 5). Built `frontend/src/components/AuthoritySearch.jsx` and mounted
  it in `App.jsx`'s top nav per the brief. Verified: `make build` clean;
  `node scripts/check_app.mjs` passed (6 pages × light/dark, no JS errors) and
  screenshots inspected by eye; a follow-up scripted Playwright pass confirmed
  click-to-navigate, Enter-to-navigate from a different page, ArrowDown+Enter selects
  the *second* match (not just the first — checked against `/api/authorities` order),
  Escape closes the dropdown, click-away closes the dropdown, and 375px width wraps to
  its own full-width row with no overlap. `make test` → 33 passed. Fixed a real bug in
  `scripts/check_app.mjs`'s own setup comment (it told you to `npm install` playwright
  inside `frontend/`, but Node resolves `node_modules` by walking up from the script's
  own folder, so that install is never found — corrected to install at the project
  root). Added `scripts/screenshots/` to `.gitignore` (generated verification output,
  not source). Next: Task 00 on the real MacBook, or continue with Task 03/05/06/10
  (all cloud-session-friendly, no Mac dependency).
- **2026-07-03 · Claude Fable 5 (handover session).** Audited repo (git clean, 2 commits
  pushed). Verified dark mode + 375px mobile rendering (screenshots, no JS errors).
  Confirmed Oxford HDT 1451% is faithful to the raw ODS (real quirk, not a bug). Added
  10 API smoke tests (`tests/test_api.py`, total now 33 passing) and
  `scripts/check_app.mjs` page-render checker. Wrote the handover pack: `CLAUDE.md`,
  this file, `docs/OPERATOR-GUIDE.md`, 12 task briefs in `docs/tasks/`, 3 skills
  (`quarterly-data-refresh`, `verify-app`, `add-metric`). Next: Task 00 on Matt's
  MacBook with Sonnet.
- **2026-07-03 · Claude Fable 5 (build session).** Built entire v1 from empty repo:
  schema/design, four pipeline sources (all real data), metric derivation + friction
  score, FastAPI backend, React frontend (6 pages), 23 tests, README, design doc.
  Verified with a full clean-state pipeline run (all sources ✅) and Playwright
  screenshots of every page. Two commits pushed to `claude/uk-planning-tracker-y687pf`.
