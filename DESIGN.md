# Design

<!-- impeccable:design-schema 1 -->

Recorded from the built world (`rebound/sim/report_html.py`), not written before it — ground truth over intention, per Impeccable's documentation discipline.

## World

**Audit dossier / evidence board.** The batch report reads as a case file, not a dashboard: numbered EXHIBITs, a case number, a chain-of-custody ledger, a signed statement — never cards, hero metrics, or a kicker above the heading.

Direction: assigned index 4 of 7 grounded candidates from the payments/audit engineer's world (seed `9f883699`, mode `operate`), raised with two donations from the catalog challenger roll: Kraftwerk's traffic-signal state vocabulary (allow/block/escalate color semantics) and the design-annual plate section's registration-mark + hairline discipline (corner crosshairs, 1px rules, mono caps). Full record: `.impeccable/surfaces/rebound-sim-report-html-py.md`.

## Palette

| Token | Value | Use |
|---|---|---|
| `--ground` | `#0a0b0d` | Page background |
| `--panel` | `#0f1114` | Verdict cells, the signed-statement block |
| `--ink` | `#e8e6df` | Primary text |
| `--dim` | `#8a8d94` | Secondary/meta text |
| `--hair` | `#26282d` | 1px rules everywhere; no shadows, no cards |
| `--amber` | `#e8a33d` | Case number, exhibit tags, crosshairs, custody-ledger hashes, `escalate` state |
| `--ok` | `#7fae6c` | `allow` state, zero-invariant verdicts |
| `--bad` | `#c06a5f` | `block` state, non-zero invariant verdicts |

Strategy: Committed (one accent — amber — carrying the document's signal weight; green/red reserved strictly for state, never decoration).

## Type

System stacks only — no fetched fonts, no CDN — a deliberate trade against the "no network requests" constraint (PRODUCT.md, Operate mode: "Operate and Read surfaces are well served by system stacks," new-work.md §4).

- Mono (`ui-monospace, SFMono-Regular, Consolas, ...`): all labels, data, hashes, case metadata — tabular numerals throughout.
- Sans (`-apple-system, Segoe UI, ...`): the H1 and prose inside the signed statement.
- Floor: 12px minimum on any line carrying real content (stage names, footer, signature); 11px reserved for genuinely atomic labels (`A1`, `EXHIBIT A`, table column heads).

## Components

- **Case header** — H1 (`Rebound — Batch Audit Report`, no eyebrow above it — the ban in craft-floor.md), right-aligned case metadata block (case number, track, scenario/ledger counts).
- **Exhibit** — the page's only section type: registration-crosshair corners (4 absolutely-positioned L-ticks, amber, 55% opacity), a tag + heading header row, hairline bottom rule.
- **Verdict block** (Exhibit A only) — 3-column grid, each cell a stamped pass/fail (`CLEAR`/`FLAGGED`), large tabular numeral colored by state.
- **Chip** — inline bordered token for allow/block/escalate counts in the disposition table; color is the only signal, border-only (no fill) to stay flat.
- **Evidence row** (citations / ledger / flags) — CSS grid rows, mono id + arrow + content, used identically across Exhibits D/E/F for one consistent "row of evidence" grammar.
- **Signed statement** — the closing AI-usage disclosure, framed as a signature block with a case-id footer line.

## Responsive

Single breakpoint at 640px: verdict grid and all evidence-row grids collapse to 1 column; the disposition table's Total column hides. Confusion-matrix rows wrap (`flex-wrap`) rather than clip — the fix for a real horizontal-overflow defect caught in mobile review.

## Provenance

No raster assets — the page has none; every mark is CSS (borders, background, `::before`/`::after`-free corner ticks as real elements). Mechanical detector (`impeccable detect.mjs`): 0 findings after three fix rounds (undersized functional text, all-caps body passages, tiny body text — see `FAILURES.md` if promoted there).
