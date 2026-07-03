# Design: UK Planning Applications Tracker

Local-first web app making English local planning authority (LPA) performance legible:
approval rates, decision speed, appeal outcomes, housing delivery — by authority and over time.

## Architecture

Two cleanly separated layers sharing only the SQLite database:

```
pipeline/   CLI-driven ETL. Downloads → data/raw cache → parse → load → derive metrics.
backend/    FastAPI app. Read-only over SQLite. Serves JSON API + built React frontend.
frontend/   React (Vite). Talks to /api/*.
config/     sources.yml (release URLs — change quarterly), settings.yml (weights, thresholds).
data/       raw/ (download cache, gitignored), reference/ (checked-in lookups), planning.sqlite.
```

The pipeline is rerun quarterly (`make pipeline`); the app never writes to the DB.
Each pipeline source is fetch → parse → load with loud failures naming the file and
sheet that broke. A failed source is skipped, recorded in `PIPELINE_STATUS.md` and in
the `pipeline_runs` table, and (if it has never loaded) backfilled with clearly-marked
sample data so the app always runs.

## Data sources

| # | Source | File(s) | Grain | Notes |
|---|--------|---------|-------|-------|
| 1 | MHCLG planning application statistics | PS1 / PS2 open-data CSVs (district matters); CPS1/CPS2 (county matters) | LPA × quarter, wide | PS1: received/decided/withdrawn, 1996→. PS2: decisions, granted, refused, speed bands and in-time counts split "excluding PAs" / "PAs only" per development type, 1979→. "PAs" = applications subject to a performance agreement (PPA / extension of time / EIA), which is what lets us measure the EOT-flattering effect. |
| 2 | PINS appeals | Casework Database + Older Casework Data (xlsx, case level) | one row per appeal | Type of Casework, ONS LPA Code, Decision Date, Decision (Allowed/Dismissed/Split...), Development Type, Reason (Refusal/Failure/...). Decisions ~2015→. |
| 3 | Housing delivery | MHCLG Live Table 122 (net additional dwellings, ODS), Housing Delivery Test measurement (ODS) | LPA × financial year | HDT gives homes required vs delivered and the official score. |
| 4 | Authority metadata | ONS Open Geography `LAD_MAY_2024_EW_BUC_RUC` (GeoJSON, generalised) + region from PS files + NOMIS population (optional) | LPA | One ArcGIS query returns boundaries **and** rural/urban classification. |

URLs live in `config/sources.yml` because gov.uk asset URLs change every release.

## Schema (SQLite)

```sql
authorities(code PK, name, region, authority_type, ruc, population, active, successor_code)
facts(authority_code, quarter, dev_type, metric, value, source)      -- long, as published
metrics(authority_code, quarter, metric, window, value)              -- derived; window 'Q'|'4Q'
annual(authority_code, year, metric, value)                          -- delivery data, FY ending `year`
boundaries(authority_code PK, geojson)                               -- one Feature per authority
pipeline_runs(source, run_at, status, message, rows_loaded)
```

Conventions:
- `quarter` is `YYYYQn` (calendar quarter as published, so `2024Q2` = Apr–Jun 2024); lexically sortable.
- Aggregates are stored in `metrics` under pseudo-codes `ENG` (England) and `REG:<region name>`.
- `dev_type` ∈ all, major, minor, other, major_res, minor_res, householder.
- `window` `Q` = single quarter, `4Q` = trailing four quarters (rolling annual).

## Local government reorganisation

PS/PINS data keeps defunct districts (e.g. Allerdale E07000026) as separate rows. A
checked-in lookup (`data/reference/authority_changes.csv`: old_code, old_name, new_code,
new_name, change_year) maps predecessors to successors for the 2009, 2019, 2020, 2021 and
2023 reorganisations. Counts are additive, so derived metrics aggregate predecessor rows
into the successor authority for pre-merger quarters, giving continuous series. Raw
`facts` keep the as-published codes. Pre-2009 legacy codes (non-GSS, e.g. `Q2908`) are
mapped by name where possible, else kept as inactive authorities excluded from rankings.
Series breaks are documented in the in-app data dictionary.

## Derived metrics (per authority × quarter, plus 4Q rolling)

From PS2, per development-type group, using columns:
`D_all` (decisions, all), `G` granted, `R` refused, `D_ex` (decisions excluding PAs),
`T_ex` (in time, excluding PAs), `D_pa` (decisions, PAs only), `T_pa` (in time, PAs only):

- `approval_rate_<dt>` = G / D_all (dt: all, major, minor, major_res, minor_res, householder)
- `pct_intime_headline_<dt>` = (T_ex + T_pa) / (D_ex + D_pa) — the published headline, which counts an agreed extended deadline as "in time"
- `pct_intime_statutory_<dt>` = T_ex / D_ex — within statutory time, agreements excluded
- `eot_share_<dt>` = D_pa / (D_ex + D_pa) — share of decisions made under an agreement
- `eot_gap_<dt>` = headline − statutory — how much agreements flatter the headline
- `decisions_<dt>`, `granted_<dt>`, `refused_<dt>`, `received_all` (PS1), `withdrawn_all`
- `decisions_vs_5yr` = 4Q decisions / mean of same authority's trailing 5-year 4Q decisions

From PINS (planning appeals with a substantive decision: Allowed / Dismissed / Split):
- `appeals_decided`, `appeals_allowed`, `appeals_dismissed`, `appeals_split`
- `overturn_rate` = allowed / decided (4Q window is the headline version)
- `appeal_rate_refusals` = appeals decided that arose from refusals / refusals (4Q)

From housing tables (annual): `net_additions`, `hdt_measure`, `hdt_required`,
`hdt_delivered` (`hdt_measure` = official HDT %, delivered/required).

### Friction score

Weighted mean of percentile ranks (0–100, higher = more planning friction) across active
English authorities, on 4Q values, with minimum-volume guards. Components and weights are
in `config/settings.yml` (defaults shown):

- inverse percentile of `approval_rate_major_res` (weight 0.40, min 10 major-res decisions/4Q)
- inverse percentile of `pct_intime_statutory_major` (0.30)
- percentile of `overturn_rate` (0.30, min 8 appeals/4Q)

The composite is always shown with its components. Missing components renormalise the
weights; an authority with no component data gets no score.

## App pages

Home (choropleth + quarter slider + metric picker) · Authority profile (time series vs
region vs England, appeals, delivery, plain-English summary) · League tables (sortable,
region/type/RUC filters, min-volume thresholds) · Compare (≤5 authorities) · National
trends · Data dictionary. Every chart: PNG + CSV export. Per-authority self-contained
HTML report at `/api/authorities/{code}/report`.

## Failure & sample-data policy

Every fetch is cached in `data/raw/` (offline reruns: `--offline`). A source that fails
to download or parse is logged loudly, recorded in `pipeline_runs`, summarised in
`PIPELINE_STATUS.md`, and the build continues. If a source has never loaded, the
`sample` source generates deterministic synthetic rows (tagged `source='sample'` and
flagged in the UI banner) so every page renders.

## Extension points (out of scope now)

- Application-level scraping of LPA portals → new pipeline source writing to a new
  `applications` table; nothing in the current schema assumes aggregate-only data.
- Wales/Scotland → `authorities.code` is GSS-ready (`W…`, `S…`); add sources + widen map.
- Hosting → backend is stateless over SQLite; put it behind any ASGI server.
