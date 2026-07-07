---
name: add-metric
description: Checklist for adding a new metric to the tracker so it appears everywhere (derivation, API, map/league pickers, dictionary) without breaking existing ones. Use for any task that introduces a new number.
---

# Add a metric

A metric only "exists" when three layers agree. Miss one and the UI shows gaps or the
dictionary lies.

## 1. Derivation — where does the number come from?

- **Quarterly count-based ratio or sum** (the normal case): add it in
  `pipeline/metrics.py` `_derive_frame()`. Rules that must hold:
  - Ratios are numerator-sum ÷ denominator-sum. NEVER average per-quarter ratios —
    the 4Q window works by summing counts first (`_rolling`) and reusing the same
    `_derive_frame`, so a correctly-written metric gets its rolling version for free.
  - Use `_safe_div` (it nulls zero denominators) and `emit(series, "metric_id")`.
  - Percentages are stored 0–100 (multiply by 100 at emit).
- **Non-additive stats (medians, percentiles per case)**: cannot go through
  `_derive_frame`. Compute in the source loader over case-level rows and pass through —
  see the design in `docs/tasks/04-appeal-timeliness-metric.md` before inventing
  anything.
- **Annual data** (per financial year): load into the `annual` table from the source
  instead; skip metrics.py entirely (profiles read `annual` directly).

New raw inputs? Extend the source parser + its fixture in `tests/fixtures/` + its test.

## 2. Catalogue — `backend/catalog.py`

Add an entry to `METRICS` (or `ANNUAL_METRICS`):

```python
"my_metric_id": {"label": "...", "unit": "%",          # % | pp | count | score | index | weeks
                 "higher_is": "good",                   # good | bad | neutral (drives ranking + map ramp colour)
                 "category": "Speed",                   # Approval | Speed | Volume | Appeals | Friction | Delivery
                 "source": MHCLG,                       # reuse the source constants
                 "description": "...", "caveats": [CAVEAT_SMALL_N]},
```

- To appear in map/league dropdowns: append the id to `RANKABLE`.
- If small denominators can produce absurd rankings: add to `MIN_DENOMINATORS`
  (`"my_metric_id": ("decisions_all", "min_decisions_4q")`) — add a new threshold to
  `config/settings.yml` `league_tables:` if none fits.
- The data dictionary page builds itself from these entries — write the description and
  caveats for Matt, plain English.

## 3. Frontend

- Pickers, map, league, dictionary: automatic via `/api/meta` once catalogued.
- Authority profile: charts are explicit — add a `<Chart data={data} a={a} metric="my_metric_id" meta={meta} />`
  in the right section of `frontend/src/pages/AuthorityPage.jsx`, and the metric id to
  `profile_metrics` in `backend/api.py` `authority_profile()`.
- New unit? Teach `fmtValue` in `frontend/src/api.js`.

## 4. Rebuild + verify

```bash
make pipeline-offline   # repopulate metrics from cached raw data (~3 min)
make build
```

Then run the **verify-app** skill in full. Additionally check:
- ENG value for the new metric is plausible; a handful of authorities have values.
- Existing metrics unchanged: England approval_rate_all before == after.
- Map renders the new metric with sensible colours in BOTH `higher_is` directions
  (bad → red ramp, good/neutral → blue).
- Dictionary entry reads sensibly.

## 5. Document

Mention the new metric in the HANDOVER session-log entry; if it changes what Matt
should glance at during refreshes, update the smell-test table in the
`quarterly-data-refresh` skill.
