"""Assembles the 11 slide+narration pairs into the final video with crossfade
transitions (video xfade + audio acrossfade), instead of hard cuts.

Run from docs/video/: python assemble_xfade.py
"""
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).parent
SLIDES = ROOT / "slides"
AUDIO = ROOT / "audio"
SCENES = [
    # Reordered per LLM council verdict (2026-09-05): the strongest, most human
    # material (the near-miss bug) was buried at position 10 in a synthesized
    # voice. It now opens the video, in the builder's real voice, so the
    # technical tour that follows plays as proof of that story rather than
    # 3 minutes of stats before any stakes exist. Scenes 2-9 and 11 are
    # deliberately left untouched (content, order, and TTS voice) -- the
    # council explicitly rejected re-recording everything or adding new
    # visual polish as low-ROI against the same-day deadline.
    "10_whatbroke", "01_title", "02_architecture", "03_tests", "04_demo_run", "05_metrics",
    "06_idempotency", "07_abstain", "08_tamper", "09_scope", "11_closing",
]
XFADE = 0.5  # crossfade duration, seconds
PAD = 0.5    # silence padding held at full opacity before/after each narration clip

def probe_duration(path: pathlib.Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main() -> None:
    durations = []
    for s in SCENES:
        wav = AUDIO / f"{s}.wav"
        d = probe_duration(wav) + PAD * 2
        durations.append(d)
        print(f"{s}: {d:.2f}s (narration {d - PAD*2:.2f}s)")

    inputs = []
    for s in SCENES:
        inputs += ["-loop", "1", "-t", str(durations[SCENES.index(s)]), "-i", str(SLIDES / f"{s}.png")]
    for s in SCENES:
        inputs += ["-i", str(AUDIO / f"{s}.wav")]

    n = len(SCENES)
    v_filters = []
    a_filters = []

    cur_v = "0:v"
    cur_a_label = None
    cur_offset = durations[0] - XFADE
    for i in range(1, n):
        next_v = f"v{i}"
        v_filters.append(f"[{cur_v}][{i}:v]xfade=transition=fade:duration={XFADE}:offset={cur_offset}[{next_v}]")
        cur_v = next_v
        cur_offset += durations[i] - XFADE

    # audio: pad each clip with silence (PAD before/after) to match video timing, then acrossfade chain
    for i, s in enumerate(SCENES):
        idx = n + i
        a_filters.append(
            f"[{idx}:a]adelay={int(PAD*1000)}|{int(PAD*1000)},apad=pad_dur={PAD}[a{i}]"
        )
    cur_a = "a0"
    for i in range(1, n):
        next_a = f"amix{i}"
        a_filters.append(f"[{cur_a}][a{i}]acrossfade=d={XFADE}:c1=tri:c2=tri[{next_a}]")
        cur_a = next_a

    filter_complex = ";".join(v_filters + a_filters)
    out_path = ROOT.parent / "rebound-demo.mp4"

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{cur_v}]", "-map", f"[{cur_a}]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        str(out_path),
        "-loglevel", "error",
    ]
    print("Running ffmpeg...")
    subprocess.run(cmd, check=True)
    total = probe_duration(out_path)
    print(f"DONE: {out_path} ({total:.2f}s)")


if __name__ == "__main__":
    main()
