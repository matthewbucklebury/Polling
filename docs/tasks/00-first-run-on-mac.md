# Task 00 — First run on Matt's MacBook

**Priority: MUST · Model: Sonnet · Depends on: nothing · Do this first.**

## Objective

Get the app fully working on Matt's MacBook Air (M3): install, run the pipeline, launch
the app, run the tests. Everything so far was built and verified on Linux; this task
proves the Mac path and fixes any small platform issues. Success = Matt can start the app
himself with one command.

## Files involved

Nothing should need changing. If something fails, the likely suspects are `Makefile`
(command availability) and `requirements.txt` (wheel availability on macOS arm64).

## Prerequisites (walk Matt through checking these first)

1. Ask Matt to open **Terminal** (Cmd+Space, type "Terminal", Enter).
2. Check tool versions — have him paste each line and report the output:
   ```bash
   python3 --version   # need 3.11 or newer
   node --version      # need 18 or newer
   git --version
   make --version
   ```
   If `python3` is missing or too old: install from https://www.python.org/downloads/
   (big yellow button). If `node` is missing: install the LTS from https://nodejs.org.
   If `make`/`git` prompt to install "command line developer tools", tell Matt to click
   **Install** and wait — that is normal and safe.
3. Clone the repo (if not already on the machine):
   ```bash
   cd ~
   git clone https://github.com/matthewbucklebury/polling.git
   cd polling
   git checkout claude/uk-planning-tracker-y687pf
   ```

## Steps

1. `make setup` — takes a few minutes. Watch for errors; warnings are fine.
2. `make test` — expect `23 passed` at this point (the 10 API tests skip until the
   database exists; the line will say `23 passed, 10 skipped` or similar).
3. `make pipeline` — downloads ~110 MB and builds the database; takes 5–10 minutes.
   Expect four `=== <source>: ok, N rows ===` lines and no `FAILED`.
4. `cat PIPELINE_STATUS.md` — every source should show ✅ ok.
5. `make test` again — expect `33 passed`.
6. `make run` — expect a line like `Uvicorn running on http://127.0.0.1:8000`.
7. Have Matt open http://127.0.0.1:8000 in his browser and do the verification below.
8. If anything needed fixing to get here, commit the fix; update
   `docs/OPERATOR-GUIDE.md` if any command Matt will use changed.

## Acceptance criteria

- `make test` prints `33 passed` on the Mac.
- `PIPELINE_STATUS.md` shows all four sources ✅.
- App serves at http://127.0.0.1:8000 and Matt completes the checks below.

## How Matt verifies this

1. Open http://127.0.0.1:8000 — a map of England appears, coloured mostly red/pink,
   titled "Friction score". **There must be NO yellow warning banner** about sample data.
2. Hover the map — council names and scores appear in a small tooltip.
3. Click any council — its profile opens with a written summary sentence and charts.
4. Click **League tables** — a ranked table appears with real council names.
5. Click **National trends** — charts appear; "The rise of extension-of-time agreements"
   should show a line climbing steeply from around 2013.
6. On a profile page click **PNG** on any chart — an image downloads. Click **CSV** — a
   spreadsheet file downloads and opens with quarters and numbers in it.
7. In Terminal press `Ctrl+C` to stop the app, then run `make run` again to prove it
   restarts cleanly.

## Do not

- Do not run the pipeline more than once if step 3 succeeded (it is idempotent but slow).
- Do not "upgrade" dependency versions to fix an install issue without recording exactly
  what changed and why in the commit message and HANDOVER session log.
- Do not touch `pipeline/metrics.py`, the parsers, or the schema — install problems
  never live there.

## Rollback

Nothing to roll back — this task changes no project code unless a platform fix is
needed. If the machine gets into a mess: `git status` to see stray files,
`git checkout -- .` to discard uncommitted edits, `rm -rf data/planning.sqlite data/raw`
and rerun `make pipeline` for a fresh database.
