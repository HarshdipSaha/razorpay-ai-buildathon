# Pitch video — script and production notes

**Final video:** `docs/rebound-demo.mp4` — 3:57, 1280×720, h264/aac.

## How it was made (reproducible, no manual recording)

Given the "no login, no API key" scope decision, a live screen recording of a
Razorpay dashboard wasn't available or honest to fake. Instead the video is
assembled deterministically from **real command output**:

1. `docs/video/build_slides.py` generates 11 styled HTML slides, each embedding
   actual captured terminal output (`pytest -q`, `python -m rebound.cli demo`,
   `verify-audit` before/after a real byte-level tamper) — not typed-up fiction.
2. Windows SAPI (`System.Speech.Synthesis`, offline, no API key) synthesizes one
   narration `.wav` per slide from `docs/video/audio/*.txt`.
3. Each HTML slide is screenshotted at 1280×720 via Playwright (served over a
   local `http.server`, since headless browsers block `file://`).
4. `docs/video/assemble.sh` pairs each slide image with its narration clip
   (`ffmpeg -loop 1 -i slide.png -i narration.wav`, padded 0.6s of silence on
   each end) and concatenates all 11 into `docs/rebound-demo.mp4`.

Regenerate with: `python docs/video/build_slides.py`, serve `docs/video/slides/`
on a local port, screenshot each `.html` to a matching `.png`, then
`bash docs/video/assemble.sh`.

## Scene breakdown (narration is verbatim from `docs/video/audio/*.txt`)

| # | Scene | Duration | What's on screen |
|---|---|---|---|
| 1 | Title / problem | 20.9s | The one-sentence problem statement |
| 2 | Architecture | 28.1s | Flow diagram + the "LLM explains, code decides" invariant |
| 3 | Tests | 7.4s | Real `pytest -q` output: 54 passed |
| 4 | Batch run | 15.8s | Real `rebound demo` output: 0 violations, 0 double charges |
| 5 | Metrics | 20.2s | 100% held-out accuracy, 5% abstain, 60/60 accounted for |
| 6 | Idempotency | 22.1s | The engineered failure: 5 duplicate webhooks, 0 double charges |
| 7 | Abstain | 24.4s | Where the system says "I don't know" instead of guessing |
| 8 | Tamper | 17.1s | Real before/after `verify-audit` output around a real byte edit |
| 9 | Scope decision | 30.3s | Why no login/API key is needed, stated explicitly |
| 10 | What broke | 25.9s | The 3 real bugs from `FAILURES.md` |
| 11 | Closing | 11.1s | Repo link, summary badges |

Total narration: 223.3s; final video with transition padding: 236.6s (3:57).
