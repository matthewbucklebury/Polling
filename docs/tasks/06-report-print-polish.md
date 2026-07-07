# Task 06 — Report & print polish

**Priority: COULD · Model: Sonnet · Depends on: Task 00.**

## Objective

The per-authority HTML report (`/api/authorities/{code}/report`) is functional but
plain. Make it a document Matt would happily print or email: friction score with its
components shown, a comparison table against region and England, page-break-friendly
print CSS. Print-to-PDF from the browser then covers the "PDF export" roadmap item.

## Files involved

- `backend/report.py` only (the report is fully server-rendered; charts are inline SVG
  built by `_svg_line`).

## Approach

1. Add a "Friction score" block after the key-figures table: the composite plus its
   three component percentiles and weights (metric ids
   `friction_approval_rate_major_res`, `friction_pct_intime_statutory_major`,
   `friction_overturn_rate`; weights live in `settings()["friction_score"]["components"]`).
2. Add a comparison column to the key-figures table: authority vs England (England
   values are in the profile payload under `series.england` — take each metric's latest
   point).
3. Print CSS inside the existing `<style>` block: `@media print` — hide nothing
   essential, avoid page breaks inside charts (`svg, table { break-inside: avoid; }`),
   set `@page { margin: 18mm; }`.
4. Verify with the API test (`tests/test_api.py::test_report_html` must keep passing)
   and by opening a report in the browser and using Print Preview.

## Acceptance criteria

- Report shows friction components with weights, and an England comparison column.
- `make test` passes.
- Print preview (Cmd+P) shows a clean multi-page document with no chart cut in half.

## How Matt verifies this

1. Open any council profile and click "Download report".
2. The report now shows the friction score with its three ingredients and weights, and
   each key figure alongside the England figure.
3. Press Cmd+P — the print preview looks like a tidy document; charts are not sliced
   across pages. Save as PDF and open it — same.

## Do not

- Do not add a PDF library or headless-browser dependency — browser print IS the PDF
  path.
- Do not change `backend/api.py` or the profile payload shape (the report consumes it;
  other pages depend on it too).

## Rollback

`git checkout -- backend/report.py`.
