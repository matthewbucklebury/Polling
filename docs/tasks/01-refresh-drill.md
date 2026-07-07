# Task 01 — Quarterly data refresh drill

**Priority: MUST · Model: Sonnet · Depends on: Task 00.**

## Objective

Practise the quarterly data refresh end-to-end so that when MHCLG/PINS publish new
quarters (roughly March, June, September, December), the refresh is routine. This drill
follows `.claude/skills/quarterly-data-refresh/SKILL.md` exactly, using whatever URLs are
current on gov.uk today. Even if no new quarter has landed since 2026Q1, the drill still
validates the whole loop (find URLs → update config → clear cache → rerun → verify).

## Files involved

- `config/sources.yml` — the only file that should change (URL values).
- `data/raw/` — cached downloads get deleted and re-fetched.
- `PIPELINE_STATUS.md` — regenerated.

## Steps

Follow the `quarterly-data-refresh` skill step by step. Summary:

1. Note the current latest quarter: `.venv/bin/python -m pipeline.cli status` and check
   the app header ("data to ...").
2. For each landing page listed in `config/sources.yml`, open it and find the current
   file URLs (the skill lists exactly which link text to look for on each page).
3. Update the `url:` values in `config/sources.yml`. **Only URLs** — do not change
   filenames or sheet names unless the skill's failure section says to.
4. Delete the superseded cached files: `rm data/raw/PS1_open_data.csv data/raw/PS2_open_data.csv data/raw/PINS_casework.xlsx data/raw/PINS_casework_older.xlsx`
   (add the housing files too if their URLs changed).
5. `make pipeline` and read the output: four `ok` lines, no `FAILED`.
6. `make test` → `33 passed`. Restart the app (`make run`).
7. Commit: config change + regenerated `PIPELINE_STATUS.md`, message like
   `Quarterly refresh: data to 2026Q2`.

## Acceptance criteria

- `PIPELINE_STATUS.md` all ✅ with a fresh timestamp.
- `make test` passes.
- The app's header shows the same or a NEWER "data to" quarter than before — never older.

## How Matt verifies this

1. Open http://127.0.0.1:8000. Top-right says "data to 2026Q1" (or newer if a new
   release was out). It must not show an older quarter than before the drill.
2. No yellow sample-data banner.
3. Open **National trends** — the charts end at the same or a later quarter than before.
4. Open any council profile — charts populated to the end, summary sentence present.

## What going wrong looks like, and what to try first

- **A download 404s / pipeline says FAILED for a source** → the URL was copied wrong or
  gov.uk moved it again. Re-open the landing page, copy the exact link address (right
  click → Copy Link), paste into `config/sources.yml`, rerun. The app keeps working on
  old data the whole time — there is no rush.
- **Pipeline "succeeds" suspiciously fast (<1 min) and nothing changed** → step 4 was
  skipped; the cache is by filename. Delete the files in `data/raw/` and rerun.
- **"expected PS2 columns missing"** → MHCLG renamed columns (rare). Stop the drill,
  log the exact error in HANDOVER.md, and make it a fresh Opus task — do not guess at
  column mappings in this session.

## Do not

- Do not edit anything except `config/sources.yml`.
- Do not delete `data/reference/` (checked-in lookups) — only `data/raw/`.
- Do not proceed to other tasks in the same session; if the drill fails, fixing it IS
  the session.

## Rollback

`git checkout -- config/sources.yml`, restore the old cache by rerunning
`make pipeline` (it re-downloads from the old URLs), done.
