# Task 04 — Appeal decision-speed metric (PINS timeliness)

**Priority: SHOULD · Model: OPUS (metric-design judgement needed) · Depends on: Task 00.**

## Objective

Add "how long do appeals take to decide in cases involving this authority" as a metric:
median weeks from PINS receiving an appeal to deciding it, per authority, rolling year.
This is a live policy topic (appeal delays) and the casework data already contains the
dates.

## Why this needs Opus

The existing derivation engine (`pipeline/metrics.py`) works exclusively on **additive
counts** rolled up over 4 quarters. A median is not additive, so this metric cannot flow
through `_derive_frame`/`_rolling`. The clean design (decided during handover, follow it
unless you find a real blocker):

- Compute medians **in the PINS source loader**, not in `metrics.py`: for each
  (authority, quarter of decision), also compute a trailing-4-quarter median over the
  case-level rows (the source has all cases in memory as a DataFrame).
- Write results directly into the `metrics` table as
  `appeal_median_weeks` (window `Q` and `4Q`) from `pins_appeals.py`, alongside the
  count facts it already loads. Compute England (`ENG`) and region (`REG:<name>`)
  medians over pooled cases the same way (pool the cases, not the medians).
  Region lookup: `SELECT code, region FROM authorities WHERE active=1`.
- **Ordering problem to handle:** `pipeline/cli.py` runs sources then `metrics.derive_all`,
  which begins with `DELETE FROM metrics`. Direct writes from the source would be wiped.
  Correct fix: have `pins_appeals.run()` stash the median rows in a module-level return
  or a small staging table (`facts` with metric `appeal_median_weeks_q`/`_4q` is
  acceptable), and make `metrics.py` copy them through verbatim at the end of
  `derive_all` (a clearly-commented passthrough block, not entangled with the count
  machinery). Choose whichever you judge cleaner; document the choice in HANDOVER.md.

## Definition (decided — do not redesign)

- Cases: same filter as existing appeal metrics (`CASEWORK_TYPES`, decided outcomes).
- Duration: `Decision Date` − `Valid Date` in days ÷ 7, rounded to 1 dp. Where
  `Valid Date` is missing fall back to `Received Date`; drop the case if both missing
  or duration is negative/&gt;520 weeks (data errors exist).
- Metric id `appeal_median_weeks`, unit `weeks` (add `"weeks"` formatting to
  `fmtValue` in `frontend/src/api.js`: show 1 dp + " wks").

## Files involved

- `pipeline/sources/pins_appeals.py` — duration computation + median aggregation.
- `pipeline/metrics.py` — passthrough only (see above).
- `backend/catalog.py` — catalogue entry (`higher_is: "bad"`, category Appeals,
  min denominator via `MIN_DENOMINATORS` → `("appeals_decided", "min_appeals_4q")`),
  add to `RANKABLE`.
- `frontend/src/api.js` — `weeks` unit formatting.
- `frontend/src/pages/AuthorityPage.jsx` — add the chart to the Appeals section.
- `tests/` — extend `tests/test_parsers.py` PINS tests: fixture already has dates;
  assert a known median from the fixture rows; add a negative-duration row to the
  fixture and assert it is dropped.
- Use the `add-metric` skill checklist.

## Acceptance criteria

- `make pipeline-offline` populates `appeal_median_weeks` for `ENG` (sanity: England
  4Q median should land somewhere in 15–45 weeks for recent years — if you get 2 or
  300, the date fields are wrong).
- Metric appears in map/league pickers, dictionary (with a caveat that duration is
  driven by PINS workload as much as by the authority), authority profiles.
- `make test` passes including the new tests; `scripts/check_app.mjs` passes.

## How Matt verifies this

1. Open the map, choose "Appeal median decision time" from the metric dropdown — the
   map colours in and the tooltip shows values like "31.0 wks".
2. Open League tables with the same metric — values are weeks, mostly between 10 and 60.
3. Open a large council's profile — the Appeals section has a new chart of median weeks.
4. Open the Data dictionary — the new metric is listed under Appeals with a caveat.

## Do not

- Do not put median logic inside `_derive_frame`/`_rolling` count machinery.
- Do not change any existing appeal metric's definition or values (compare a council's
  overturn rate before/after your change — must be identical).
- Do not use `LPA Decision Date` (that's the original application decision, not the appeal).

## Rollback

Revert the touched files; `make pipeline-offline` regenerates metrics without the new
rows; `make build`.
