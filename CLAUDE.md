# UK Planning Applications Tracker — standing context

Local-first web app making English local planning authority (LPA) performance legible:
approval rates, decision speed (including how extension-of-time agreements flatter it),
appeal outcomes, housing delivery. Single user (Matt) today; designed to become public later.

**Matt (the operator) cannot read code.** He runs commands you give him, clicks around the
app, and reports what he sees. Every task must end with verification he can perform by
looking at the screen, and every explanation to him must be plain English.

## Architecture in one paragraph

A CLI pipeline (`pipeline/`) downloads official statistics (URLs in `config/sources.yml`,
raw files cached in `data/raw/`), parses them, loads a long-format `facts` table in
`data/planning.sqlite`, and derives ~4M metric rows (quarterly + rolling-annual, with
England/region aggregates and a configurable friction score from `config/settings.yml`).
A read-only FastAPI backend (`backend/`) serves `/api/*` plus the built React frontend
(`frontend/dist/`). Pipeline and app share only the SQLite file. Full design:
`docs/DESIGN.md`. Handover state, backlog and risks: **`docs/HANDOVER.md` — read it at
the start of every session.**

## Key commands

```bash
make setup              # one-time: python venv + pip + npm install
make pipeline           # fetch → parse → load → derive (quarterly; ~6 min, needs network)
make pipeline-offline   # re-parse from data/raw cache, no network
make build              # build the React frontend into frontend/dist/
make run                # build if needed + serve http://127.0.0.1:8000
make test               # pytest: parser fixtures + derivation + API smoke tests (needs built DB for API part)
node scripts/check_app.mjs   # page-render check against a RUNNING app (light+dark, screenshots, fails on JS errors)
```

Always use the project venv (`.venv/bin/python`); system pip cannot build odfpy on
Debian-patched setuptools. A healthy `make test` prints `33 passed`.

## Hard rules

1. **Never mark a task done without running its verification steps** (at minimum
   `make test` and, for UI changes, `node scripts/check_app.mjs` with the app running,
   plus the task brief's "How Matt verifies this" steps yourself first).
2. **Do not refactor these without an explicit task brief:** `pipeline/metrics.py`
   (rolling/ratio maths — ratios must stay sum-of-counts over the window, never means of
   ratios), `pipeline/sources/mhclg_applications.py` (`_ps2_wanted_columns` mirrors real
   MHCLG column names), `data/reference/authority_changes.csv` (reorganisation lookup —
   tests depend on specific chains), `backend/catalog.py` metric ids (frontend and
   dictionary reference them by name).
3. **Never hand-edit** `PIPELINE_STATUS.md` (generated), anything in `data/raw/`
   (download cache), or `frontend/dist/` (build output).
4. The database is **~1.2 GB by design** (two ~4M-row tables + indexes). Do not
   "optimise" it, add compression, or change the schema outside task 07.
5. New metrics must be added in all three places together: derivation
   (`pipeline/metrics.py`), catalogue (`backend/catalog.py`), and they then appear in the
   data dictionary automatically. Use the `add-metric` skill.
6. Quarterly data refresh follows the `quarterly-data-refresh` skill exactly — in
   particular, **delete the superseded files from `data/raw/` after changing URLs**, or
   the pipeline silently reuses stale cached data.
7. Commit after every completed task with a descriptive message; push to
   `claude/uk-planning-tracker-y687pf` unless Matt says otherwise. Never force-push.
8. Sample data (`pipeline/sample_data.py`) only ever backfills a dataset that is
   completely empty and always shows a UI banner — never widen its use to paper over a
   partial load.

## Session-close protocol (binding)

Before ending ANY session:
1. Update `docs/HANDOVER.md`: current-state changes, tick/annotate the backlog, append a
   dated entry to the Session log (what was done, what was verified, what's next).
2. Only mark a task done if its acceptance criteria and verification steps actually
   passed — otherwise log it as in-progress with exact symptoms.
3. `git add -A && git commit` (message says what changed and how it was verified) and
   `git push -u origin claude/uk-planning-tracker-y687pf`.
4. Tell Matt in plain English: what changed, how you proved it, and which task to run
   next session.
