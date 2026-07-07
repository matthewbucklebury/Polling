# Task 07 — Slim the 1.2 GB database (optional)

**Priority: COULD · Model: OPUS · Depends on: Task 00. Skip unless disk space or query
speed actually becomes a problem.**

## Objective

`data/planning.sqlite` is ~1.2 GB: `metrics` (4.0M rows + 3 indexes ≈ 745 MB) and
`facts` (3.5M rows + 2 indexes ≈ 426 MB). Everything works fine at this size; this task
exists only if it starts to hurt. Target: under ~500 MB without changing any API
response.

## Decided constraints (do not violate)

- No API response may change (the full `tests/test_api.py` suite is the contract).
- The pipeline must remain a from-scratch rebuild (no migrations — the DB is
  disposable; `make pipeline` recreates it).
- Parsers and derivation maths are untouched; this is storage layout only.

## Sanctioned ideas, in order of preference

1. **Drop `Q`-window metric rows for quarters before `display_from_quarter`** (2004Q2,
   from `config/settings.yml`) — the UI never requests them; 4Q rows must be kept for
   all years because national trends start at 2004 but roll from 1979 counts. Estimate:
   removes ~35% of `metrics`.
2. **Trim `idx_metrics_a`/`idx_metrics_mq`**: check with `EXPLAIN QUERY PLAN` which
   queries in `backend/api.py` actually use each index; drop any index no query uses.
3. **Facts pruning**: `facts` rows with `value = 0` for the six speed-band metrics
   (`band1..band6`) are ~a third of facts and only feed derivation, never the API.
   They could be skipped at load — BUT only if derivation output is proven identical
   (see verification), because `sum(min_count=…)` logic in `metrics.py` distinguishes
   missing from zero. This is the risky one; attempt last or not at all.
4. `VACUUM` at the end of `pipeline/cli.py run` (cheap, reclaims free pages).

## Verification (the whole task hinges on this)

1. BEFORE changing anything: dump a reference of derived output —
   ```bash
   .venv/bin/python -c "
   import sqlite3; c=sqlite3.connect('data/planning.sqlite')
   rows=c.execute(\"SELECT * FROM metrics WHERE quarter>='2004Q2' ORDER BY authority_code,quarter,metric,window\").fetchall()
   import hashlib; print(len(rows), hashlib.sha256(str(rows).encode()).hexdigest())"
   ```
   Record count + hash in the session notes.
2. After changes + full `make pipeline-offline` rebuild: rerun the same command. The
   hash must be IDENTICAL (for idea 1, compare only `window='4Q'` rows plus `Q` rows
   ≥ 2004Q2 — i.e. exactly what remains).
3. `make test` (33 passing) and `node scripts/check_app.mjs`.
4. `du -h data/planning.sqlite` before/after — record both in HANDOVER.md.

## How Matt verifies this

1. In Terminal: `du -h data/planning.sqlite` — the reported size is meaningfully
   smaller than 1.2G (the session will tell you the expected number).
2. Click through the app exactly as in Task 00's verification list — everything looks
   identical to before: same numbers on the same councils.

## Do not

- Do not switch database engines, add compression extensions, or change column types.
- Do not "while I'm here" refactor `metrics.py` — layout only.
- Abort the task (revert everything) if the hash check cannot be made to pass.

## Rollback

`git checkout -- .` then `make pipeline-offline` rebuilds the original DB from cache.
