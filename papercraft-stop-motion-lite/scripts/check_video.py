#!/usr/bin/env python3
"""Final gate for a delivered MP4. Prints PASS/FAIL lines and writes a contact sheet.

  python3 scripts/check_video.py out/final.mp4 --dur 120 [--contact work/contact.jpg]

Checks: duration ±0.1 s, H.264 + yuv420p, AAC present with real sound, loudness about -14 LUFS,
no quiet (nearly frozen) span longer than 2 s, full decode without errors.
"""
import argparse
import json
import re
import subprocess
import sys

import numpy as np


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--contact", default="work/contact.jpg")
    ap.add_argument("--quiet", type=float, default=0.15, help="mean abs frame diff (0-255) treated as frozen")
    a = ap.parse_args()
    res = []
    ok = lambda c, m: res.append(("PASS " if c else "FAIL ") + m)

    info = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", a.video]).stdout)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    ok(abs(dur - a.dur) <= 0.1, f"duration {dur:.2f}s (want {a.dur})")
    ok(v and v["codec_name"] == "h264" and v.get("pix_fmt") == "yuv420p", f"video {v and v['codec_name']} {v and v.get('pix_fmt')}")
    ok(au is not None and au["codec_name"] == "aac", f"audio {au and au['codec_name']}")

    if au:
        r = run(["ffmpeg", "-nostats", "-i", a.video, "-map", "0:a", "-af", "ebur128", "-f", "null", "-"])
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
        lufs = float(m[-1]) if m else -99
        ok(-16.5 <= lufs <= -12.5, f"loudness {lufs} LUFS (want about -14)")

    dec = run(["ffmpeg", "-v", "error", "-i", a.video, "-f", "null", "-"])
    ok(not dec.stderr.strip(), "decodes cleanly" + ("" if not dec.stderr.strip() else ": " + dec.stderr[:200]))

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-vf", "fps=12,scale=160:90,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 90, 160).astype(np.int16)
    diff = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    per_s = np.array([diff[i * 12:(i + 1) * 12].mean() for i in range(len(diff) // 12)])
    worst, run_len, start = 0, 0, 0
    for i, x in enumerate(per_s):
        run_len = run_len + 1 if x < a.quiet else 0
        if run_len > worst:
            worst, start = run_len, i - run_len + 1
    ok(worst <= 2, f"longest frozen span {worst}s" + (f" from {start}s" if worst else ""))
    res.append(f"INFO median motion {np.median(per_s):.2f} (Milo reference ~1.5-2.0; below 0.8 feels static)")

    run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", "fps=1/3,scale=384:-1,tile=8x6", "-frames:v", "1", a.contact])
    res.append(f"INFO contact sheet {a.contact} — open it and look at every shot")
    print("\n".join(res))
    sys.exit(1 if any(r.startswith("FAIL") for r in res) else 0)


if __name__ == "__main__":
    main()
