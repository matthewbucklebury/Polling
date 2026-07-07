---
name: verify-app
description: Standard verification pass for this project - run after ANY change, before claiming a task done. Tests, page-render check with screenshots, and the numbers smell-test.
---

# Verify the app

Run all three layers. A task is not done until all pass.

## 1. Automated tests

```bash
make test
```

Healthy: everything passed, nothing failed (33 tests as of 2026-07-03; the count grows
over time). API tests skip if `data/planning.sqlite` doesn't exist — build it with
`make pipeline` first if your change touches data or backend.

## 2. Page-render check (for any frontend, backend or data change)

```bash
make build                 # if frontend files changed
make run &                 # or run in a second terminal / background task
node scripts/check_app.mjs
```

(First time on a machine: `cd frontend && npm install --no-save playwright`; on a Mac
also `npx playwright install chromium`. In Claude remote sessions Chromium is already
at /opt/pw-browsers/chromium.)

Healthy: `PASSED — all 6 pages rendered in light and dark with no JS errors.`
Then actually LOOK at `scripts/screenshots/*.png` with the Read tool — the script only
catches JS errors, not visual breakage. Check: nothing overlapping, charts have lines,
map has coloured regions, dark variants legible.

## 3. Numbers smell-test (for any pipeline/metrics change)

England-level values that must stay in familiar ranges (rolling year, recent quarters):

```bash
.venv/bin/python -c "
import sqlite3; c = sqlite3.connect('data/planning.sqlite')
q = c.execute(\"SELECT MAX(quarter) FROM metrics WHERE authority_code='ENG' AND metric='approval_rate_all' AND window='4Q'\").fetchone()[0]
for m in ['approval_rate_all','eot_share_all','overturn_rate','pct_intime_statutory_major','decisions_all']:
    v = c.execute(\"SELECT value FROM metrics WHERE authority_code='ENG' AND metric=? AND window='4Q' AND quarter=?\", (m,q)).fetchone()
    print(f'{m:35} {v[0] if v else None}')"
```

Expected (as of data to 2026Q1): approval ~87, EOT share ~40, overturn ~32,
statutory-major ~86, decisions ~295,000. Anything an order of magnitude off means the
change broke derivation — stop and diff `pipeline/metrics.py`.

## 4. Report the evidence

When telling Matt a task is done, quote: the test summary line, the check_app PASSED
line, and which "How Matt verifies this" steps you performed yourself with what you saw.
