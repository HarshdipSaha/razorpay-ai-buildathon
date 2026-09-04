# Pitch video — script and production notes

**Final video:** `docs/rebound-demo.mp4` — 3:05, 1280×720, h264/aac, crossfade transitions between scenes.

## How it was made (fully reproducible, no screen recording)

Given the "no login, no API key" scope decision, a live screen recording of a Razorpay dashboard wasn't available or honest to fake. The video is assembled deterministically from real command output and a real screenshot of the product's own report page:

1. **Copy** (`docs/video/_copydesk_final.md`): written with the `copydesk-write` skill, then run through independent prose and craft review passes (banned-phrase / AI-pattern check; concrete-first-opening, naming, and central-point-dwelling check). Named the core mechanism ("words, not wallets") and revised Scene 10 and Scene 11 based on that review before locking the final copy.
2. **Slides** (`docs/video/build_slides.py`): 11 HTML slides, each a genuinely different composition (no repeated kicker-plus-card template), pulling color/type directly from the product's real UI (`rebound/sim/report_html.py`'s audit-dossier design). Scene 5 embeds a real screenshot of the actual redesigned report page, not a mockup. Reviewed and rebuilt by a dedicated subagent against `impeccable`'s craft-floor bans (no eyebrow/kicker labels, no same-template repetition, no overflow/cramming) — one fix round, confirmed by screenshotting all 11 slides at 1280×720 and reading them back.
3. **Narration**: Windows SAPI (`System.Speech.Synthesis`, offline, no API key) synthesizes one `.wav` per scene from `docs/video/audio/*.txt`.
4. **Assembly** (`docs/video/assemble_xfade.py`): pairs each slide image with its narration clip, padded with silence, and chains all 11 through `ffmpeg`'s `xfade` (video) and `acrossfade` (audio) filters for smooth crossfade transitions instead of hard cuts — the technique borrowed from a reference demo video the user pointed to.

Regenerate with: `python docs/video/build_slides.py` (rewrites slide HTML from `_copydesk_final.md`), screenshot each `.html` to a matching `.png` in `docs/video/slides/` at 1280×720, regenerate narration via the PowerShell SAPI snippet in `aidlc-docs/process-log.md`, then `python docs/video/assemble_xfade.py`.

## Scene breakdown (narration verbatim from `docs/video/audio/*.txt` / `_copydesk_final.md`)

| # | Scene | Narration length | What's on screen |
|---|---|---|---|
| 1 | Title | 20.1s | The one-sentence problem statement, centered, spare |
| 2 | Architecture | 24.2s | "Words, not wallets" — a single flow diagram, no cards |
| 3 | Tests | 7.5s | Real `pytest -q` output: 54 passed |
| 4 | Batch run | 13.5s | A 3-up verdict strip (0 violations, 0 double charges, 4 escalated) echoing the real report's Exhibit A |
| 5 | The report | 18.1s | Real screenshot of the redesigned audit-dossier report page |
| 6 | Idempotency | 16.8s | The engineered failure: 5 duplicate webhooks in, 0 double charges out |
| 7 | Abstain | 12.3s | Where the system says "I don't know" instead of guessing |
| 8 | Tamper | 14.3s | Real before/after `verify-audit` output around a real byte edit |
| 9 | Scope decision | 19.3s | Why no login/API key is needed, as inline facts not a bullet dump |
| 10 | What broke | 22.9s | 3 bugs, weighted, the one that actually mattered singled out |
| 11 | Closing | 9.9s | Case-file callback ("CASE CLOSED"), repo link, summary stats |

Total narration: 178.7s; final video with crossfade transitions: 184.7s (3:05).
