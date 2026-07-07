# Task 11 — Housing targets vs delivery (standard method)

**Priority: COULD · Model: OPUS (data availability research + judgement) · Depends on:
Task 03 (HDT history).**

## Objective

Show each authority's net additions against its housing *target*. The original project
brief asked for "housing targets under the standard method where published". The catch:
there is no single stable MHCLG live table of standard-method numbers; figures moved
with the Dec-2024 NPPF (new standard method). This task is research-first: find a
citable source, then load it.

## Phase A — research (do this before writing any code)

1. Look for an official machine-readable publication of standard-method local housing
   need per LPA. Candidates to check, in order:
   - MHCLG's "local housing need" table published alongside the Dec 2024 NPPF
     (gov.uk; there was an ODS of indicative numbers per LPA).
   - The HDT files already loaded — their "homes required" column IS a served target
     (capped/adjusted); Task 03 gives it per year. A defensible fallback: plot net
     additions against HDT homes-required ÷ 3 per year.
   - planning.data.gov.uk datasets.
2. Write your findings and decision into `docs/plans/TARGETS.md` (source, caveats,
   chosen approach). If no official per-LPA standard-method file can be verified,
   **use the HDT-derived fallback and say so in the data dictionary** — do not scrape
   third-party sites (LPA consultancies publish their own recalculations; not citable).

## Phase B — implement (same session if Phase A resolves quickly)

- New annual metric(s): `housing_target` (per FY) in the `annual` table, loaded by
  `pipeline/sources/housing_delivery.py` from whichever source Phase A chose.
- Profile page: extend the existing "Net additional dwellings" chart with a dashed
  target line (second series, `--muted`, dashed — same pattern as England lines in
  other charts) and a sentence in the delivery card ("delivered X% of target over the
  last three years").
- Catalogue/dictionary entries with the caveat chosen in Phase A.
- Tests: extend the housing fixtures with a target row; assert the loaded value.

## Acceptance criteria

- `docs/plans/TARGETS.md` records the source decision with URLs.
- Profiles show delivery vs target; dictionary explains exactly what "target" means.
- `make test` green; check_app green; no change to existing net-additions values.

## How Matt verifies this

1. Open a well-known under-deliverer's profile (try searching "Epping" or a London
   borough): the net additions chart now has a dashed "target" line, and the delivery
   card says what share of target was delivered.
2. Open the Data dictionary → Delivery: a "Housing target" entry explains where the
   number comes from in plain English.

## Do not

- Do not scrape consultancy or news sites for target numbers.
- Do not present HDT "homes required" as "the standard method number" — label it
  faithfully (it is the HDT requirement, which caps and adjusts).
- Do not modify `hdt_measure`/`net_additions` loading.

## Rollback

Revert touched files; `make pipeline-offline`; delete `docs/plans/TARGETS.md` if abandoning.
