# Task 08 — Wales scoping study (research only, no code)

**Priority: COULD · Model: OPUS · Depends on: nothing. Output is a document, not code.**

## Objective

Produce `docs/plans/WALES.md`: an honest assessment of what adding Wales would take.
Wales was explicitly out of scope for v1 because its statistics are a different system.
This task is research and planning ONLY — no parser, schema or frontend changes.

## Questions the document must answer

1. **Applications data**: What does StatsWales publish on planning applications by
   Welsh LPA (received/decided/granted, speed, by development type)? At what grain and
   from what year? Exact dataset names/URLs and whether a machine-readable
   (CSV/OData) route exists.
2. **Appeals**: PINS handled Welsh appeals historically; PEDW (Planning and Environment
   Decisions Wales) handles them now. Is Wales in the existing PINS casework files
   (check the actual downloaded xlsx for W-prefixed ONS codes — the file is in
   `data/raw/`)? What does PEDW publish?
3. **Delivery/targets**: Welsh equivalents of net additions (StatsWales dwellings
   estimates) — HDT does not apply in Wales; what's the nearest concept?
4. **Boundaries/metadata**: Welsh LADs are in the same ONS service already used
   (`LAD_MAY_2024_EW_BUC_RUC` — the current query filters `LAD24CD LIKE 'E%'`); RUC
   coverage for Wales; population via NOMIS.
5. **Comparability**: Which metrics would be comparable with England (approval rate?)
   and which would NOT (speed definitions differ; extension-agreement equivalents?).
   Recommend whether Wales appears in the same league tables or segregated views.
6. **Schema fit**: confirm `authorities.code` W-codes, region = 'Wales', and where
   ENG-style aggregates would need a `WAL` pseudo-code.
7. **Effort estimate**: number of single-session tasks, ordered, each with a one-line
   brief, sized like the existing `docs/tasks/` briefs.

## Method

Use web search/fetch against gov.wales, statswales.gov.wales, PEDW pages; inspect the
already-downloaded PINS files for Welsh rows. Cite every claim with a URL. Where a
dataset's existence can't be confirmed, say so plainly — an honest "unknown" beats a
guessed URL.

## Acceptance criteria

- `docs/plans/WALES.md` exists, answers all seven questions with sources, and ends with
  a go/no-go recommendation and a task list.
- No code files changed (`git status` shows only the new doc).
- HANDOVER.md backlog updated: either new Wales tasks added (if "go") or Task 08 marked
  done with "no-go for now" and the reason.

## How Matt verifies this

Open `docs/plans/WALES.md` (the session can print it in chat too) and read it. You
should be able to understand every section. It must end with a clear recommendation
sentence: either "worth doing, roughly N sessions" or "not worth it because …".

## Do not

- Write no code. Change no config. This session produces one markdown file.

## Rollback

Delete the doc.
