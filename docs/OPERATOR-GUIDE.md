# Operator guide — for Matt

This is your manual for running Claude sessions on this project. No technical knowledge
needed. Keep this open in a tab.

## The golden rules

1. **One task per session.** Start a fresh chat for each task. Don't let one chat run
   for hours across multiple tasks — long chats make the model forgetful and sloppy.
2. **The model must prove its work, and you verify it too.** Every task file has a
   "How Matt verifies this" section. Do those steps yourself before considering a task
   done. If verification fails, the task is not done, whatever the model says.
3. **Everything lives in the repo.** If a session taught you something important, ask
   the model to write it into `docs/HANDOVER.md` before the session ends.

## Starting a session

Open Claude Code in the project folder, then paste exactly this (change the task
number):

> Read CLAUDE.md and docs/HANDOVER.md, then do the task in docs/tasks/02-authority-search.md.
> Follow the session-close protocol in CLAUDE.md before you finish.

For your very first session tomorrow, the task is `00-first-run-on-mac.md`.

If you just want to look at the app without a task, you don't need Claude at all:
open Terminal, type `cd ~/polling` then `make run`, and go to http://127.0.0.1:8000
in your browser. Press Ctrl+C in Terminal to stop it.

## Which model to pick

- **Sonnet** for any task whose file says "Model: Sonnet". This is most tasks.
- **Opus** only for tasks marked "Model: OPUS", or when a Sonnet session got genuinely
  stuck and you're retrying. Opus uses up your plan much faster — don't spend it on
  routine work.

## How to tell a task really succeeded

All three must be true:

1. The model showed test results in the chat: look for a line like **`33 passed`**
   (the number may grow over time — what matters is "passed" and **zero "failed"**).
2. You performed the task file's "How Matt verifies this" steps and saw what it
   describes.
3. The model committed and pushed: the end of the chat should mention a commit, and
   you can confirm by pasting `git log --oneline -3` into Terminal — the top line
   should describe the work just done.

## Warning signs — stop the session

Stop (say: "Stop. Update docs/HANDOVER.md with exactly where things stand, commit what
is safe, and tell me what to do next.") if you see any of these:

- The model hits the **same error three times** in a row with slightly different fixes.
- It says "this should work now" **without showing test output or telling you what to
  click**.
- It starts editing files the task file didn't mention, especially anything under
  `pipeline/` when the task is about the frontend (or vice versa).
- It proposes to "clean up", "refactor", or "simplify" things outside the task.
- Huge unexplained output: hundreds of lines of changes for a small task.
- It wants to delete or rewrite `docs/`, `CLAUDE.md`, or `data/reference/` files.

After stopping, start a FRESH session with: *"Read CLAUDE.md and docs/HANDOVER.md. The
last session on task NN got stuck — read its session-log entry, then continue carefully."*
Use Opus for the retry if the failed session was Sonnet.

## When something breaks — what to paste

Copy-paste is your superpower. Give the new session:

1. **The exact command you ran** (copy the line you typed).
2. **The last ~30 lines of Terminal output** — always include the very last line, and
   anything containing `Error`, `FAILED`, or `Traceback`.
3. **What the browser shows**: the address bar URL and a plain description ("the map
   page is blank below the title", "there's a yellow banner saying sample data").
4. If the app shows an error page, copy all of its text.

Example message:

> Something's wrong. I ran `make pipeline` and it ended with this: [paste]. The app
> still opens but the header says "data to 2025Q4" when it said 2026Q1 before. Read
> CLAUDE.md and docs/HANDOVER.md, look at the risk register, and fix it.

## Routine things you'll do

- **Quarterly data refresh** (roughly March / June / September / December, when new
  planning statistics come out): start a session with
  *"Read CLAUDE.md and docs/HANDOVER.md, then do the quarterly-data-refresh skill."*
  This is also Task 01 the first time.
- **Just using the app**: `make run` in Terminal, browse, Ctrl+C to stop.
- **Checking overall health any time**: paste `make test` into Terminal. All "passed"
  and no "failed" = healthy. (Some tests "skip" if the app database isn't built —
  that's fine.)

## Things you should never do

- Don't edit any file yourself except this kind of documentation — one stray character
  in a code or config file can break the app in ways you can't see.
- Don't delete anything inside `data/reference/` (small lookup files the app needs).
  Deleting `data/raw/` or `data/planning.sqlite` is safe — they rebuild — but let a
  session do it.
- Don't run commands from the internet or from memory; use the ones in this guide or
  ones a session gives you in context.
