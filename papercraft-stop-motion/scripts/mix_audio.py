#!/usr/bin/env python3
"""Mix narration, foley and score from work/sound.json and mux with the silent video.

  python3 scripts/mix_audio.py work/sound.json out/video_silent.mp4 out/final.mp4

sound.json:
{
  "dur": 120.0,
  "music": {"file": "audio/score.wav", "gain_db": -18, "duck_db": -8, "silence": [[82.3, 83.8]]},
  "vo":    [{"t": 1.2, "file": "audio/vo/L1.wav"}],
  "foley": [{"t": 6.1, "file": "audio/foley/paper_land.wav", "gain_db": -6}]
}
Checks: every file exists, VO lines do not overlap and end before dur. Output: -14 LUFS, true peak -1.5 dBTP,
AAC 192k, H.264 copied, +faststart. Never writes or reads API keys.
"""
import json
import subprocess
import sys
from pathlib import Path


def probe_dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    plan_path, video, out = sys.argv[1:]
    plan = json.load(open(plan_path))
    dur = float(plan["dur"])
    inputs, filters, labels, errors = [], [], [], []

    vo = sorted(plan.get("vo", []), key=lambda v: v["t"])
    end_prev = 0.0
    for v in vo:
        if not Path(v["file"]).exists():
            errors.append(f"missing {v['file']}")
            continue
        d = probe_dur(v["file"])
        if v["t"] < end_prev + 0.2:
            errors.append(f"VO {v['file']} at {v['t']}s overlaps previous line ending {end_prev:.2f}s")
        end_prev = v["t"] + d
        if end_prev > dur:
            errors.append(f"VO {v['file']} ends {end_prev:.2f}s after film end {dur}s")
    for f in plan.get("foley", []):
        if not Path(f["file"]).exists():
            errors.append(f"missing {f['file']}")
    if errors:
        sys.exit("\n".join("FAIL " + e for e in errors))

    def add(file, t, gain_db, label):
        idx = 1 + sum(1 for x in inputs if x == "-i")  # input 0 is the video
        inputs.extend(["-i", file])
        ms = int(round(t * 1000))
        filters.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain_db}dB,"
                       f"adelay={ms}|{ms}[{label}]")
        labels.append(label)

    for i, v in enumerate(vo):
        add(v["file"], v["t"], v.get("gain_db", 0), f"vo{i}")
    for i, f in enumerate(plan.get("foley", [])):
        add(f["file"], f["t"], f.get("gain_db", -6), f"fx{i}")
    m = plan.get("music")
    if m:
        idx = 1 + sum(1 for x in inputs if x == "-i")
        inputs.extend(["-stream_loop", "-1", "-i", m["file"]])
        vol = [f"volume={m.get('gain_db', -18)}dB"]
        for a, b in m.get("silence", []):
            vol.append(f"volume=enable='between(t,{a},{b})':volume=0")
        # duck under narration
        for v in vo:
            d = probe_dur(v["file"])
            vol.append(f"volume=enable='between(t,{v['t']},{v['t'] + d})':volume={m.get('duck_db', -8)}dB")
        filters.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur},"
                       + ",".join(vol) + ",afade=t=out:st=" + f"{max(dur - 2, 0)}:d=2[mus]")
        labels.append("mus")
    if not labels:
        sys.exit("FAIL nothing to mix")
    filters.append("".join(f"[{l}]" for l in labels) +
                   f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{dur},"
                   "loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", video] + inputs + [
        "-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", str(dur), "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
