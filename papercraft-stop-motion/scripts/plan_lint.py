#!/usr/bin/env python3
"""Lint a papercraft film timesheet for story-film density before any costly generation.

Checks shot count and size mix, background variety, action-beat density, distinct action
sheets, depth-lane coverage, vertical/depth actions and the longest single-beat hold.
Prints OK or a list of FAIL/WARN lines and exits 1 on any FAIL.
"""
import argparse
import json
import sys
from collections import Counter

# (min shots, min beats, min distinct sheets, min depth/vertical actions) per 120 s, scaled by runtime.
PER_120 = dict(shots=12, beats=48, sheets=16, depth=8)
FLOOR = dict(shots=4, beats=12, sheets=6, depth=3)
DEPTH_WORDS = ("jump", "hop", "climb", "sit", "lie", "crouch", "toward", "away", "turn", "ride",
               "fly", "float", "swim", "fall", "slide", "dive", "roll")
MAX_HOLD = 2.5   # seconds per beat before the hero must change action, lane or prop state
MAX_SHOT = 12.0  # seconds per shot


def need(key, dur):
    return max(FLOOR[key], round(PER_120[key] * dur / 120.0))


def lint(plan):
    out = []
    dur = float(plan["dur"])
    shots = sorted(plan["shots"], key=lambda s: s["t"])
    fail = lambda m: out.append("FAIL " + m)
    warn = lambda m: out.append("WARN " + m)

    if abs(shots[-1]["t1"] - dur) > 0.05 or abs(shots[0]["t"]) > 0.05:
        fail(f"shots span {shots[0]['t']}–{shots[-1]['t1']} s, expected 0–{dur} s")
    for a, b in zip(shots, shots[1:]):
        if abs(a["t1"] - b["t"]) > 0.05:
            fail(f"gap/overlap between {a['name']} and {b['name']}")

    if len(shots) < need("shots", dur):
        fail(f"{len(shots)} shots < {need('shots', dur)} for {dur:.0f} s")
    sizes = Counter(s.get("size") for s in shots)
    for sz in ("wide", "medium", "close-up"):
        if dur >= 25 and not sizes.get(sz):
            fail(f"no {sz} shot")
    bgs = Counter(s.get("bg") for s in shots)
    if len(bgs) < max(2, round(4 * dur / 120)):
        fail(f"only {len(bgs)} backgrounds")
    for bg, n in bgs.items():
        if n >= 3:
            warn(f"background {bg} used {n}×; add an angle or reuse with distinct strips and camera")
    for s in shots:
        if s["t1"] - s["t"] > MAX_SHOT:
            warn(f"{s['name']} lasts {s['t1'] - s['t']:.1f} s; consider a cut")
    for a, b in zip(shots, shots[1:]):
        if a.get("bg") == b.get("bg") and a.get("size") == b.get("size"):
            fail(f"jump cut {a['name']} → {b['name']} (same bg and size)")

    beats, sheets, lanes, depth_n, prev = [], set(), set(), 0, None
    longest = (0.0, "")
    for s in shots:
        bs = sorted(s.get("beats", []), key=lambda b: b["t"])
        if not bs:
            fail(f"{s['name']} has no beats")
            continue
        if abs(bs[0]["t"] - s["t"]) > 0.05:
            fail(f"{s['name']}: first beat at {bs[0]['t']} s, shot starts {s['t']} s")
        ends = [b["t"] for b in bs[1:]] + [s["t1"]]
        for b, e in zip(bs, ends):
            hold = e - b["t"]
            if hold > longest[0]:
                longest = (hold, f"{s['name']}@{b['t']:.1f}s {b['sheet']}")
            key = (b["sheet"], b.get("lane"), b.get("prop"))
            if key != prev:
                beats.append(b)
            prev = key
            sheets.add(b["sheet"])
            lane = str(b.get("lane", "mid"))
            lanes.add("surface" if lane.startswith("surface") else lane)
            ys = [p[1] for p in b.get("path", []) if p[1] is not None]
            if any(w in b["sheet"] for w in DEPTH_WORDS) or lane.startswith("surface") or \
                    (len(ys) >= 2 and abs(ys[-1] - ys[0]) >= 0.05):
                depth_n += 1

    if len(beats) < need("beats", dur):
        fail(f"{len(beats)} action beats < {need('beats', dur)}")
    if len(sheets) < need("sheets", dur):
        fail(f"{len(sheets)} distinct action sheets < {need('sheets', dur)}")
    if not {"back", "mid", "front"} <= lanes:
        fail(f"lanes used {sorted(lanes)}; need back, mid and front")
    if depth_n < need("depth", dur):
        fail(f"{depth_n} depth/vertical actions < {need('depth', dur)}")
    if longest[0] > MAX_HOLD:
        fail(f"longest beat {longest[0]:.1f} s at {longest[1]} (> {MAX_HOLD} s)")

    out.append(f"INFO {len(shots)} shots {dict(sizes)}, {len(bgs)} bgs, {len(beats)} beats, "
               f"{len(sheets)} sheets, lanes {sorted(lanes)}, {depth_n} depth actions, longest beat {longest[0]:.1f} s")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("timesheet")
    plan = json.load(open(ap.parse_args().timesheet))
    lines = lint(plan)
    for line in lines:
        print(line)
    if any(l.startswith("FAIL") for l in lines):
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
