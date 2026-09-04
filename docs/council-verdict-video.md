# LLM Council — pitch video fix (2026-09-05)

User's own reaction after watching `docs/rebound-demo.mp4`: "looks very technical, voice is more AI-ish... shouldn't only look like and show technical stuff... not that attention-grabbing." Asked the council to debate and fix it, with the five advisors including an explicit product-owner lens and an explicit technical-feasibility lens.

## Where the Council Agrees
All five advisors independently rejected the user's own framing. "Too technical" is not the problem — for a Razorpay engineering hiring panel, terminal output, pytest runs, and a tamper-detection demo are load-bearing evidence, not a liability. The real, converging diagnosis: **no human is audibly or visibly present**, and the first-person script ("I built...", "I caught it by hand...") read by a synthesized voice is a *credibility mismatch*, not a content problem. All five also independently flagged the same buried asset: Scene 10 ("what broke") is the strongest material in the video — it maps directly to the brief's "failure recovery, read first" criterion — yet it sat second-to-last, delivered in the same flat TTS as everything else. Every peer review, unprompted, named the Expansionist's answer strongest: recut Scene 10 as a cold open, in real voice, before the title card.

## Where the Council Clashes
The Executor wanted a contained fix (re-record audio only, don't touch structure) given deadline risk. Everyone else wanted Scene 10 promoted to the cold open. All five peer reviews sided against the Executor here — not because the risk-awareness was wrong, but because dismissing the reorder ignored that it's the highest-value content sitting in the worst position.

## Blind Spots the Council Caught
Every single reviewer, independently, flagged the same gap none of the five advisors raised on their own: **nobody proposed a backup.** No one suggested keeping the current working video safe before touching the pipeline — ironic, given "failure recovery" is literally the judged criterion.

## The Recommendation
1. Back up the current video before touching anything.
2. Re-record **only Scene 1 and Scene 10's narration** in a real human voice — not all 11 scenes.
3. Recut Scene 10 as the opening, before the title card: lead with the near-miss, then title, then the technical tour plays as proof of that story.
4. Leave scenes 2–9 and 11 exactly as-is — content, order, and TTS voice. Do not reorder further, add a face-cam, or chase generic "attention-grabbing" polish.
5. Quick-check the written failure narrative for consistency with the new opening.

## The One Thing to Do First
Back up the working video before touching anything.

## What was executed immediately after the verdict
- `docs/rebound-demo.backup-3m05s.mp4` — the pre-fix video, kept as a submit-safe fallback.
- `docs/video/assemble_xfade.py` — `SCENES` list reordered, `10_whatbroke` now first.
- `docs/video/audio/10_whatbroke.txt` — rewritten as a cold-open hook, leading with the near-miss (previously the third item in a flat list).
- `docs/submission.md` — the council's own consistency check surfaced a **real stale error**: "25% of the batch" (a rounded figure from before an earlier copydesk pass) was still in the written failure narrative; corrected to "15 of the 60 scenarios" to match the video and `FAILURES.md`.
- **Blocked on the user's own voice recording** for Scene 1 and Scene 10 — this is the one part of the fix that cannot be done by the AI without reintroducing the exact TTS-credibility problem being solved.
