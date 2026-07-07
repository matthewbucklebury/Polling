---
name: quarterly-data-refresh
description: Refresh the tracker's data when MHCLG/PINS publish a new quarter (roughly Mar/Jun/Sep/Dec). Updates URLs in config/sources.yml, clears the stale cache, reruns the pipeline, verifies, commits.
---

# Quarterly data refresh

Do these steps in order. The app keeps working on old data throughout — nothing here is
destructive until verified.

## 1. Record the starting point

```bash
.venv/bin/python -m pipeline.cli status
```

Note each source's status and the current latest quarter (also shown in the app header,
"data to …"). You must end this workflow with the same or a newer quarter, never older.

## 2. Find the new file URLs

For each source, open the landing page (also recorded in `config/sources.yml`) and copy
the link address of the named file:

| Config key | Landing page | Link to copy |
|---|---|---|
| `mhclg_applications.files.ps1` | https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics | "PS1 data - open data table" CSV (the FULL one, not "last four quarters") |
| `mhclg_applications.files.ps2` | same page | "PS2 data - open data table" CSV (full, not last-four-quarters) |
| `pins_appeals.files.casework` | https://www.gov.uk/government/publications/planning-inspectorate-appeals-database | "Casework Database - <Month Year>" xlsx |
| `pins_appeals.files.casework_older` | same page | "Older Casework Data - <Month Year>" xlsx |
| `housing_delivery.files.net_additions` | https://www.gov.uk/government/statistical-data-sets/live-tables-on-net-supply-of-housing | "Live Table 122" ODS (annual — only changes each November) |
| `housing_delivery.files.hdt` | https://www.gov.uk/government/collections/housing-delivery-test | latest measurement ODS (only if a NEW measurement was published) |
| `authority_meta.*` | rarely changes | only touch after a local government reorganisation |

If a landing page has moved, search gov.uk's API:
`curl -sSL "https://www.gov.uk/api/search.json?q=<terms>&count=10"`.

## 3. Update config and clear the stale cache

Edit ONLY the `url:` values in `config/sources.yml`. Then delete the superseded cached
files — **this step is mandatory; the cache is by filename and the pipeline will
silently reuse stale files otherwise**:

```bash
rm -f data/raw/PS1_open_data.csv data/raw/PS2_open_data.csv \
      data/raw/PINS_casework.xlsx data/raw/PINS_casework_older.xlsx
# plus Live_Table_122.ods / HDT file if those URLs changed
```

## 4. Rerun and verify

```bash
make pipeline        # ~6 min; expect four "=== <source>: ok, N rows ===" lines
cat PIPELINE_STATUS.md   # every source ✅
make test            # expect all passed, none failed
```

Then start the app (`make run`) and check http://127.0.0.1:8000:
- Header shows the new quarter ("data to 2026Q2" etc.), never an older one.
- No yellow sample-data banner.
- National trends charts extend to the new quarter.
- One spot-check profile (e.g. /authority/E07000223) has charts to the new quarter.

Sanity numbers that should stay in familiar ranges (rolling year, England, on the
Trends page): approval rate ~85–90%, extension-agreement share 35–50%, appeals allowed
25–35%. Wildly different values mean a parse went wrong — stop and investigate before
committing.

## 5. If a source fails

- The pipeline skips it and keeps everything else; `PIPELINE_STATUS.md` shows ❌ with
  the file that broke. Fix the URL and rerun — reruns are cheap.
- "expected PS2 columns missing …" = MHCLG renamed columns. Do NOT guess: log the exact
  error in `docs/HANDOVER.md` (risk register points to `_ps2_wanted_columns()` in
  `pipeline/sources/mhclg_applications.py`) and raise it as a dedicated Opus task.

## 6. Commit

```bash
git add config/sources.yml PIPELINE_STATUS.md
git commit -m "Quarterly refresh: data to <NEW QUARTER>"
git push -u origin claude/uk-planning-tracker-y687pf
```

Update `docs/HANDOVER.md`'s session log per the session-close protocol.
