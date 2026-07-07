# Task 09 — County matters (minerals & waste applications)

**Priority: COULD · Model: OPUS (double-counting judgement) · Depends on: Task 01 done at
least once (you'll fetch new files).**

## Objective

County councils decide "county matters" (minerals, waste, their own developments) —
currently excluded. Load the CPS1/CPS2 open-data CSVs so county councils get profiles
and appear in league tables as their own authority type, WITHOUT contaminating district
totals or England aggregates.

## The one rule that matters

**County-matters decisions must never be added into England/region aggregates or mixed
into district-level metrics.** MHCLG's district PS1/PS2 already covers all district
matters; adding CPS on top would double-count categories of decisions in national
figures that currently reconcile with published totals. The clean design (follow it):

- Load CPS facts with `source='cps1'/'cps2'` under the county council's own E10 code.
- In `pipeline/metrics.py` `_load_canonical_facts`, the England/region aggregation
  filters `code.str.match(r"^E0[6789]")` — E10 county codes are already excluded by
  that regex. Verify this and add a test proving ENG totals are unchanged after CPS
  load (load the fixture, derive, compare an ENG value).
- `authority_type='county'` (add `"E10": "county"` to `AUTH_TYPE_BY_PREFIX`), so league
  tables can include/exclude them via the existing type filter; they have no LAD
  boundary so the map is unaffected.

## Files involved

- `config/sources.yml` — CPS1/CPS2 open-data CSV URLs (they sit on the same MHCLG
  landing page as PS1/PS2; look for `CPS1_data_-_open_data_table` / `CPS2…`).
- `pipeline/sources/mhclg_applications.py` — the CPS files share the PS layout
  (`Region,LPANM,LPACD,Quarter`, same column-name grammar). Inspect the real header
  first: `head -6 data/raw/CPS1_open_data.csv | cut -c1-400`. Reuse `_read`/melt
  machinery; the wanted-columns map will be smaller (county matters have fewer
  development types — build it from the actual header, fail loudly on missing).
- `tests/` — fixture excerpts + tests, same pattern as PS fixtures.
- `backend/catalog.py` — no new metrics needed; existing ones apply.

## Acceptance criteria

- County councils (e.g. Kent E10000016, Hampshire) appear in `/api/authorities` with
  type `county` and have working profile pages with approval/speed charts.
- **England aggregates unchanged**: `ENG` `decisions_all` for 2024Q4/4Q identical
  before and after (record the number before you start).
- League tables: counties appear only when the type filter includes them; default views
  look unchanged.
- `make test` green, `scripts/check_app.mjs` green.

## How Matt verifies this

1. Open League tables, set "Authority type" to "county" — county councils like Kent and
   Hampshire appear with values.
2. Set the filter back to "All types", metric "Applications decided" — the top of the
   table looks the same as before this task (no county suddenly at #1).
3. Open the National trends page — the England volume chart is identical to before
   (same shape, same end value; compare against an old PNG export if unsure).
4. Click a county council's name — a profile page opens with charts.

## Do not

- Do not add counties to the map (no boundaries loaded for E10; leaving them off is
  correct and already explained in the map sidebar).
- Do not modify how PS1/PS2 load — additions only.
- Do not proceed if ENG totals change — that is the double-counting failure mode; stop
  and re-read "The one rule that matters".

## Rollback

Revert touched files, `DELETE FROM facts WHERE source IN ('cps1','cps2')` via a rerun:
`git checkout -- . && make pipeline-offline`.
