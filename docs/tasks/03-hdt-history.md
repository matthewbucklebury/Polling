# Task 03 — Load Housing Delivery Test history (2018–2022)

**Priority: SHOULD · Model: Sonnet · Depends on: Task 00.**

## Objective

Only the 2023 HDT measurement is loaded. MHCLG published measurements for 2018, 2019,
2020, 2021 and 2022 too. Loading them turns the single HDT number on each profile into a
trend and lets Task 11 (targets vs delivery) build on real history.

## Files involved

- `config/sources.yml` — turn the single `hdt` entry into `hdt_2018` … `hdt_2023`
  entries (same structure, one per file).
- `pipeline/sources/housing_delivery.py` — loop over all `hdt_*` config entries instead
  of the single `hdt` key. `parse_hdt()` already reads the measurement year from the
  file's own title, so it should need no changes — each file loads under its own year.
- `frontend/src/pages/AuthorityPage.jsx` — the "Housing Delivery Test" card currently
  shows the latest year; add a small line chart of `hdt_measure` by year when more than
  one year exists (copy the "Net additional dwellings" chart pattern right above it).
- `tests/test_parsers.py` — existing HDT tests must still pass unchanged.

## Finding the URLs

Each year has a publication page:
`https://www.gov.uk/government/publications/housing-delivery-test-<YEAR>-measurement`
for 2018–2023. On each page, grab the ODS/XLSX "measurement" file URL (the same way
`config/sources.yml` documents for other sources). **Watch out:** the older files
(2018/2019) may be XLSX rather than ODS and may have slightly different column wording.
`parse_hdt` matches columns by regex (`total number of homes required` etc.) and reads
the year from the title — if a file fails, print its first 8 rows
(`pd.read_excel(path, sheet_name=0, header=None, nrows=8)`) and adjust the regexes
minimally, keeping all existing tests green.

## Steps

1. Add the config entries with real URLs (verify each downloads: the pipeline caches
   into `data/raw/` under distinct filenames like `HDT_2018.ods`).
2. Update `run()` in `housing_delivery.py` to iterate every config key starting with
   `hdt`. Keep failures per-file loud (SourceError naming the file).
3. `make pipeline` (or `.venv/bin/python -m pipeline.cli run --source housing_delivery`
   for speed). Check: `annual` table now has `hdt_measure` rows for years 2018–2023.
   Quick check command:
   ```bash
   .venv/bin/python -c "
   import sqlite3; c=sqlite3.connect('data/planning.sqlite')
   print(c.execute(\"SELECT year, count(*) FROM annual WHERE metric='hdt_measure' GROUP BY year\").fetchall())"
   ```
   Expect ~300 authorities per year, one row per year 2018–2023.
4. Frontend chart, `make build`, `make test`, `node scripts/check_app.mjs`.
5. If a specific year's file cannot be parsed after one honest attempt, load the years
   that work, note the gap in HANDOVER.md, and finish — partial history is still a win.

## Acceptance criteria

- `annual` has `hdt_measure` for ≥4 measurement years.
- Existing tests pass (`make test`); the profile page shows an HDT trend for a large
  authority (e.g. `/authority/E07000178` Oxford).
- The report endpoint still returns 200 (covered by `tests/test_api.py`).

## How Matt verifies this

1. Open any council profile (e.g. search/click to Oxford).
2. The Housing Delivery Test card now shows a small chart with several years of scores,
   not just a single 2023 number.
3. The number for 2023 is the same as it was before this task (compare against the
   report you downloaded previously if unsure — Oxford 2023 is 1451%, which is correct).

## Do not

- Do not change how the 2023 file is parsed or its loaded values — additions only.
- Do not touch `pipeline/metrics.py` (HDT lives in the `annual` table, not `metrics`).
- Do not invent URL patterns — verify each URL actually downloads before committing it.

## Rollback

Revert the three files (`git checkout -- config/sources.yml pipeline/sources/housing_delivery.py frontend/src/pages/AuthorityPage.jsx`),
delete the new `data/raw/HDT_*` files, rerun `--source housing_delivery`.
