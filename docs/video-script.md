# Pitch video — script and production notes

**Final video:** `docs/rebound-demo.mp4` — 3:48, 1280×720, h264/aac, crossfade transitions between scenes. Narrated by Microsoft Zira (offline SAPI) via SSML with explicit pause breaks, opening on the "what broke" cold open per the LLM council verdict (`docs/council-verdict-video.md`). The prior 3:05 David-voice cut is kept as `docs/rebound-demo.backup-3m05s.mp4`.

## How it was made (fully reproducible, no screen recording)

Given the "no login, no API key" scope decision, a live screen recording of a Razorpay dashboard wasn't available or honest to fake. The video is assembled deterministically from real command output and a real screenshot of the product's own report page:

1. **Copy** (`docs/video/_copydesk_final.md`): written with the `copydesk-write` skill, then run through independent prose and craft review passes (banned-phrase / AI-pattern check; concrete-first-opening, naming, and central-point-dwelling check). Named the core mechanism ("words, not wallets") and revised Scene 10 and Scene 11 based on that review before locking the final copy.
2. **Slides** (`docs/video/build_slides.py`): 11 HTML slides, each a genuinely different composition (no repeated kicker-plus-card template), pulling color/type directly from the product's real UI (`rebound/sim/report_html.py`'s audit-dossier design). Scene 5 embeds a real screenshot of the actual redesigned report page, not a mockup. Reviewed and rebuilt by a dedicated subagent against `impeccable`'s craft-floor bans (no eyebrow/kicker labels, no same-template repetition, no overflow/cramming) — one fix round, confirmed by screenshotting all 11 slides at 1280×720 and reading them back.
3. **Narration**: Windows SAPI (`System.Speech.Synthesis`, offline, no API key) synthesizes one `.wav` per scene from `docs/video/audio/*.txt`.
4. **Assembly** (`docs/video/assemble_xfade.py`): pairs each slide image with its narration clip, padded with silence, and chains all 11 through `ffmpeg`'s `xfade` (video) and `acrossfade` (audio) filters for smooth crossfade transitions instead of hard cuts — the technique borrowed from a reference demo video the user pointed to.

Regenerate with: `python docs/video/build_slides.py` (rewrites slide HTML from `_copydesk_final.md`), screenshot each `.html` to a matching `.png` in `docs/video/slides/` at 1280×720, regenerate narration via the PowerShell SAPI snippet in `aidlc-docs/process-log.md`, then `python docs/video/assemble_xfade.py`.

## Scene breakdown (narration verbatim from `docs/video/audio/*.txt` / `_copydesk_final.md`)

Play order below is the council's reorder: the "what broke" scene opens the video as a cold-open hook, ahead of the title card. File names keep their original numbering (`10_whatbroke` still plays first) so the pipeline stays stable.

| Play # | File | Scene | Narration | What's on screen |
|---|---|---|---|---|
| 1 | `10_whatbroke` | Cold open: what broke | 31.2s | 3 bugs, weighted; the one that actually mattered singled out |
| 2 | `01_title` | Title | 28.1s | The one-sentence problem statement, centered, spare |
| 3 | `02_architecture` | Architecture | 26.3s | "Words, not wallets" — a single flow diagram; names "the wallet gate" |
| 4 | `03_tests` | Tests | 10.0s | Real `pytest -q` output: 54 passed |
| 5 | `04_demo_run` | Batch run | 16.4s | A 3-up verdict strip echoing the real report's Exhibit A |
| 6 | `05_metrics` | The report | 22.3s | Real screenshot of the redesigned audit-dossier report page |
| 7 | `06_idempotency` | Idempotency | 21.0s | 5 duplicate webhooks in, 0 double charges out |
| 8 | `07_abstain` | Abstain | 12.8s | Where the system says "I don't know" instead of guessing |
| 9 | `08_tamper` | Tamper | 18.6s | Real before/after `verify-audit` output around a real byte edit |
| 10 | `09_scope` | Scope decision | 21.8s | Why no login/API key is needed |
| 11 | `11_closing` | Closing | 13.4s | "CASE CLOSED" callback, repo link, summary stats; echoes "the wallet gate" |

Total narration: 221.9s (incl. SSML pauses); final video with crossfade transitions: 228.1s (3:48).
