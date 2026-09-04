# Inception · Stage 0 — Workspace Detection

**Date:** 2026-09-04
**Result:** **Greenfield.**

## What was found

| Path | Contents |
|---|---|
| `docs/hackathon-spec.md` | Captured brief of the Razorpay AI Buildathon (tracks, bar, evaluation criteria, form fields). Not code. |
| `.playwright-mcp/` | Browser snapshot cache left by the Playwright MCP during spec capture. Tooling artefact — git-ignored and removed. |
| (git) | The folder sat inside a stray repository rooted at `H:\`. A fresh repository was initialised inside the project folder so the buildathon submission has its own clean history. |

No source code, no dependency manifests, no existing architecture to reverse-engineer → **greenfield path**; brownfield reverse-engineering is skipped.

## External constraints inherited into the baseline

From `docs/hackathon-spec.md`:

- Submission deadline **5 September 2026** (one-shot Google Form; no edits after submit).
- Deliverables: **public GitHub repo**, **5-minute pitch video**, written **"what broke and how you got out"** narrative, resume.
- Evaluation: problem taste · build quality · AI judgment (incl. where AI was *not* used) · failure recovery.
- Every track's bar: measured batch metrics, bounded/gated money actions, audit trail, at least one failure handled gracefully. Track 2 is strictly defense-only.
- Razorpay **test-mode APIs** are the integration surface.

## Next stage

`01-requirements.md` — blocked on idea selection (research forks → candidate ideas → LLM council). See `process-log.md`.

---
*Approval gate for this stage: see `audit.md` → Gate I-0.*
