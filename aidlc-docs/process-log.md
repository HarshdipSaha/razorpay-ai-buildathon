# Process Log — every AI skill and tool used to build this

Chronological. This is the "how it was actually made" record the buildathon asks for. Each entry names the tool/skill, what it was pointed at, what came out, and — where relevant — what went wrong.

All work driven through **Claude Code** (Anthropic's CLI agent). Times are IST, 2026-09-04 unless stated.

| # | When | Skill / tool | Used for | Output / outcome |
|---|---|---|---|---|
| 1 | ~07:45 | **Playwright MCP** (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill_form`) | Scrape razorpay.com/buildathon (single-page site) and walk the Google Form's pages to capture exact submission fields | `docs/hackathon-spec.md`. Form pages 1–2 captured; the auto-mode permission classifier blocked further form clicks, so page 3 fields came from the user's own paste. **Did not submit anything.** |
| 2 | ~07:50 | **Persistent memory** (file-based) | Save hackathon facts (deadline, tracks, eligibility quirk: grad-year dropdown offers only 2027–29) for future sessions | `razorpay-ai-buildathon.md` in memory store |
| 3 | ~08:00 | **`/academic-research-skills:ars-3w`** (deep-research, three-way-scan mode) | Entry point for research-grounded ideation | Reframed into two parallel research streams (below) |
| 4 | ~08:00 | **`AskUserQuestion`** | Disambiguate target hackathon (command text mentioned AWS docs; two live hackathons) | User: Razorpay AI Buildathon → recorded in `audit.md` |
| 5 | ~08:02 | **Forked subagent A** (agent-swarm *peer-parallel*) + **`WebSearch`** | Market scan per track: pain + evidence, incumbents, gap | Brief: Tracks 2 & 4 crowded by funded incumbents (Chargeflow/Justt; BlackLine/HighRadius). **Track 3 strongest gap** — no tool unifies root-cause diagnosis across the failure funnel. Track 1 gap: merchant-side agent-compliance gate. |
| 6 | ~08:02 | **Forked subagent B** + **`arxiv` skill** + **`duckduckgo-search` skill** | Academic scan: WHY/HOW/WHAT of 4–6 recent papers on payment fraud, agentic commerce safety, reconciliation agents, recovery workflows, bounded agent actions | *(pending at time of writing)* |
| 7 | ~08:05 | **`SendMessage`** to running subagent A | **Course correction:** user clarified AWS is irrelevant → dropped the AWS-building-blocks section mid-flight; redirected to a Razorpay test-mode API capability scan | Recorded in `audit.md`. Subagent A had already finished; its AWS section was discarded. |
| 8 | ~08:10 | **`/ai-dlc`** | Adopt AI-DLC as the build methodology; begin **Inception** | `aidlc-docs/` scaffold (this file, `inception/00-workspace-detection.md`, `registry.md`, `audit.md`) |
| 9 | ~08:12 | **`gh` CLI** + git | Fresh repo inside project folder (parent folder was inside a stray `H:\`-rooted repo); public GitHub repo created because submission requires a public URL | *(see commit history)* |

## Planned next

| Skill / tool | Purpose |
|---|---|
| **`llm-council`** (5 independent AI advisors, anonymous peer review, synthesized verdict) | Pressure-test 3–4 candidate ideas; pick one. If the council rejects, iterate with a new candidate. |
| **AI-DLC Inception** stages 1–2 | `01-requirements.md`, `02-application-design.md` with approval gates |
| **AI-DLC Efforts** `001…` | Construction, one effort per unit; parallel subagents where units are independent |
| **`verification-before-completion`** | Evidence before any "it works" claim — metrics on a batch, not a happy-path demo |

## Where AI was deliberately *not* used

*(to be filled during construction — the buildathon's "AI judgment" criterion explicitly rewards this)*
