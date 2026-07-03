# UK Planning Applications Tracker

A local-first web app that makes English local planning authority performance legible:
**approval rates, decision speed, appeal outcomes and housing delivery — by authority and
over time.** Python/FastAPI + SQLite backend, React frontend, and a separate CLI data
pipeline that downloads and cleans the official statistics each quarter.

## Mocked or skipped

Nothing is mocked in the current build — all four sources loaded real data:

- ✅ MHCLG planning application statistics (PS1/PS2 open data, 1979→, all English LPAs)
- ✅ Planning Inspectorate appeals casework database (case level, decisions 2016→)
- ✅ MHCLG Live Table 122 (net additional dwellings) + Housing Delivery Test 2023
- ✅ ONS boundaries + rural/urban classification; NOMIS population

Deliberately out of scope (documented in the in-app data dictionary): county-matters
returns (CPS1/CPS2, minerals & waste), pre-2009 legacy authorities that cannot be mapped
to a successor, Wales and Scotland. If a source ever fails overnight it is skipped, logged
in [`PIPELINE_STATUS.md`](PIPELINE_STATUS.md), and clearly-marked synthetic sample data
keeps the app runnable (a banner appears in the UI).

## Quick start

Requires Python 3.11+ and Node 18+ (tested on macOS Apple Silicon and Linux).

```bash
make setup       # one-time: venv + pip install + npm install
make run         # builds the frontend, runs the pipeline if no DB, serves http://127.0.0.1:8000
```

The first pipeline run downloads ~110 MB of official statistics into `data/raw/`
(kept as an offline cache) and takes a few minutes to build `data/planning.sqlite`.

## The app

| Page | What it shows |
|---|---|
| **Map** | England choropleth on any metric with a rolling-year quarter slider; click through to profiles |
| **Authority profile** | All core metrics vs region and England, appeals record, delivery record, a plain-English summary generated from the data, and a self-contained HTML report download |
| **League tables** | Sortable rankings on any metric with region / authority-type / rural-urban filters and minimum-volume thresholds |
| **Compare** | Overlay up to five authorities on any metric (England always shown) |
| **National trends** | England-wide series: the long decline in decision volumes, the rise of extension-of-time agreements, headline vs statutory speed, appeals |
| **Data dictionary** | Every metric's definition, source table and caveats (EOT distortion, COVID anomalies, reorganisation breaks) |

Every chart exports as PNG and its data as CSV.

### The metrics worth knowing about

- **Headline vs statutory speed.** The government's headline "% in time" counts decisions
  made within an *agreed extended* deadline as in time. ~40% of decisions now happen under
  such agreements (single digits in 2013), so the app always computes speed both ways and
  shows the gap (`eot_gap_*`) and the agreement share (`eot_share_*`).
- **Friction score.** A composite of percentile ranks: low major-residential approval
  (weight 0.40), slow statutory-basis major decisions (0.30), high appeal overturn rate
  (0.30). Weights and minimum denominators live in `config/settings.yml`; components are
  always displayed alongside the composite.
- **Reorganisation handling.** Predecessor districts are summed into successor unitaries
  (2009–2023 changes, lookup in `data/reference/authority_changes.csv`) so series are
  continuous.

## Quarterly rerun

MHCLG and PINS publish quarterly; asset URLs on gov.uk change with every release.

1. Open the landing pages listed in `config/sources.yml` and copy the new file URLs into
   the matching `url:` fields (filenames/sheets rarely change; parsers fail loudly naming
   the file and sheet if a layout does change).
2. Delete the superseded cached files from `data/raw/` (or the pipeline will keep using them —
   the cache is by filename), then:

```bash
make pipeline    # fetch → parse → load → derive metrics → PIPELINE_STATUS.md
```

3. Check `PIPELINE_STATUS.md` (also surfaced in the app) for anything that failed.

`make pipeline-offline` re-parses from the cache with no network — useful when iterating
on parsers. `python -m pipeline.cli run --source pins_appeals` reruns one source.

## Layout

```
pipeline/    CLI ETL: sources/{mhclg_applications,pins_appeals,housing_delivery,authority_meta}.py,
             metrics.py (derivation + friction score), sample_data.py, cli.py
backend/     FastAPI: api.py, catalog.py (metric definitions), summary.py, report.py
frontend/    React (Vite): map, profiles, league tables, compare, trends, dictionary
config/      sources.yml (release URLs), settings.yml (friction weights, thresholds)
data/        raw/ (download cache, gitignored) · reference/ (checked-in lookups) · planning.sqlite
tests/       parser + derivation tests over fixture files in tests/fixtures/
docs/        DESIGN.md — schema and pipeline design
```

Run tests with `make test`. The DB schema and metric conventions are in
[`docs/DESIGN.md`](docs/DESIGN.md).

## Roadmap

Left as clean extension points, deliberately not built yet:

- **Application-level data** scraped from individual LPA planning portals — add a new
  pipeline source writing to a new table; nothing assumes aggregate-only data.
- **Wales and Scotland** — different statistical systems; `authorities.code` is GSS-ready
  (`W…`/`S…`), so this is new sources plus a wider map extent.
- **Hosting/deployment** — the backend is a stateless reader over SQLite; any ASGI host
  works. Multi-user features (accounts, saved comparisons) would come after that.
- Possible next metrics: PINS decision timeliness, s106/CIL context, local plan status.
