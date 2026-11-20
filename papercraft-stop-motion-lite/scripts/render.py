#!/usr/bin/env python3
"""Render a papercraft stop-motion film from work/timesheet.json without writing compositing code.

The model only edits JSON. This script handles depth lanes, lane scaling, paths, jump arcs,
pose cycling on twos, contact shadows, parallax strips, camera push/pan, colour grade,
props, vocabulary cards and bilingual subtitles, and pipes frames to ffmpeg (silent video).

  python3 scripts/render.py work/timesheet.json out/video_silent.mp4
  python3 scripts/render.py work/timesheet.json work/stills --stills 2.0 15.5 40  # PNG stills only
  python3 scripts/render.py work/timesheet.json out/test.mp4 --from 30 --to 45   # partial render

See references/timesheet-format.md for every field.
"""
import argparse
import json
import math
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

LOOP_WORDS = ("walk", "run", "swim", "fly", "float", "paddle", "tiptoe", "sneak", "skip", "idle", "ride")
ARC_WORDS = ("jump", "hop", "leap")
SIZE_H = {"wide": 0.36, "medium": 0.48, "close-up": 0.78}  # hero height / frame height in the mid lane
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "C:/Windows/Fonts/msjhbd.ttc",
]

ROOT = Path(".")


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def font_path(cli):
    for p in [cli, os.environ.get("PAPERCRAFT_FONT")] + FONT_CANDIDATES:
        if p and os.path.exists(p):
            return p
    sys.exit("No CJK font found. Pass --font /path/to/font.ttc")


@lru_cache(maxsize=None)
def load_rgba(path):
    p = ROOT / path
    if not p.exists():
        sys.exit(f"missing image: {p}")
    return Image.open(p).convert("RGBA")


@lru_cache(maxsize=None)
def load_sheet(sheet):
    """Return (tiles, anchors, ref_h). Tiles come from work/tiles/<sheet>/ in sheet.json order."""
    d = ROOT / "work" / "tiles" / sheet
    meta = d / "sheet.json"
    if not meta.exists():
        sys.exit(f"missing {meta} — slice the sheet with split_sheet.py first")
    entries = json.loads(meta.read_text())
    tiles = [load_rgba(str(d / e["file"])) for e in entries]
    anchors = [tuple(e["base_anchor"]) for e in entries]
    ref_h = max(t.height for t in tiles)
    return tiles, anchors, ref_h


def scaled(img, k):
    k = max(k, 0.01)
    return img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)


class Shot:
    def __init__(self, s, W, H):
        self.s, self.W, self.H = s, W, H
        lanes = {"back": 0.66, "mid": 0.80, "front": 0.93}
        lanes.update(s.get("lanes", {}))
        self.lanes = lanes
        self.surfaces = s.get("surfaces", {})
        self.hero_h = s.get("hero_h", SIZE_H.get(s.get("size", "wide"), 0.36)) * H
        self.beats = sorted(s["beats"], key=lambda b: b["t"])

    def lane_y(self, lane):
        if lane.startswith("surface:"):
            return self.surfaces[lane.split(":", 1)[1]]
        return self.lanes[lane]

    def lane_scale(self, y_frac):
        return (y_frac / self.lanes["mid"]) ** 1.6

    def beat_at(self, t):
        cur = 0
        for i, b in enumerate(self.beats):
            if b["t"] <= t + 1e-6:
                cur = i
        b = self.beats[cur]
        end = self.beats[cur + 1]["t"] if cur + 1 < len(self.beats) else self.s["t1"]
        return cur, b, end


def hero_state(shot, t, fps):
    """Position (x px, y frac), lift px, pose image, anchor, scale, flip, lane for time t."""
    i, b, end = shot.beat_at(t)
    dur = max(end - b["t"], 1e-3)
    u = (t - b["t"]) / dur
    lane = str(b.get("lane", "mid"))
    path = b.get("path")
    if not path:  # stand still: explicit x, else where the last moving beat ended, else centre
        x, y0 = b.get("x"), None
        for prev in reversed(shot.beats[:i]):
            if prev.get("path"):
                px, py = prev["path"][-1]
                x = px if x is None else x
                y0 = py if str(prev.get("lane", "mid")) == lane else None
                break
        path = [[shot.W / 2 if x is None else x, y0 if y0 is not None else shot.lane_y(lane)]]
    path = [[p[0], p[1] if p[1] is not None else shot.lane_y(lane)] for p in path]
    if len(path) == 1:
        x, y = path[0]
        dx = 0
    else:
        e = ease(u) if b.get("ease", True) else u
        seg = min(int(e * (len(path) - 1)), len(path) - 2)
        v = e * (len(path) - 1) - seg
        x = lerp(path[seg][0], path[seg + 1][0], v)
        y = lerp(path[seg][1], path[seg + 1][1], v)
        dx = path[-1][0] - path[0][0]
    tiles, anchors, ref_h = load_sheet(b["sheet"])
    n = len(tiles)
    drawing = int(round((t - b["t"]) * fps)) // 2  # on twos
    loop = b.get("loop", any(w in b["sheet"] for w in LOOP_WORDS))
    k = drawing % n if loop else min(int(u * n), n - 1)
    lift = 0.0
    if b.get("arc", any(w in b["sheet"] for w in ARC_WORDS)) and len(path) > 1:
        lift = math.sin(math.pi * ease(u)) * b.get("arc_h", 0.15) * shot.H
    flip = b.get("flip", dx < -1)
    scale = shot.hero_h / ref_h * shot.lane_scale(y) * b.get("scale", 1.0)
    return dict(x=x, y=y, lift=lift, img=tiles[k], anchor=anchors[k], scale=scale, flip=flip, lane=lane)


def paste_anchor(canvas, img, anchor, x, y_px, k, flip):
    im = scaled(img, k)
    ax, ay = anchor[0] * k, anchor[1] * k
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
        ax = im.width - ax
    canvas.alpha_composite(im, (int(round(x - ax)), int(round(y_px - ay))))


def shadow(canvas, x, y_px, w, lift, strength=0.35):
    w = max(int(w * (1 - min(lift / 400, 0.5))), 8)
    h = max(w // 6, 4)
    sh = Image.new("RGBA", (w * 2, h * 4), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((w // 2, h * 1.5, w * 1.5, h * 2.5), fill=(30, 20, 10, int(255 * strength)))
    sh = sh.filter(ImageFilter.GaussianBlur(h / 2))
    canvas.alpha_composite(sh, (int(x - w), int(y_px - h * 2)))


def place_layer(canvas, path, W, H, shift):
    img = load_rgba(path)
    if img.width != W:
        img = scaled(img, W * 1.1 / img.width)
    canvas.alpha_composite(img, (int((W - img.width) / 2 + shift), H - img.height))


def grade(frame, warm):
    """warm in [-1, 1]: negative cools and dims (rain, setback), positive warms (payoff)."""
    if not warm:
        return frame
    a = np.asarray(frame).astype(np.float32)
    w = float(warm)
    a[..., 0] *= 1 + 0.08 * w
    a[..., 2] *= 1 - 0.08 * w
    if w < 0:
        a[..., :3] *= 1 + 0.12 * w
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def draw_text_layer(frame, t, plan, fonts, W, H):
    d = ImageDraw.Draw(frame)
    big, mid, small = fonts
    for c in plan.get("cards", []):
        if c["t0"] <= t < c["t1"]:
            pop = ease((t - c["t0"]) / 0.25)
            pad = int(28 * pop)
            ew = d.textlength(c["en"], font=big)
            zw = d.textlength(c["zh"], font=mid)
            bw, bh = max(ew, zw) + 2 * pad + 20, int(big.size * 1.25 + mid.size * 1.3 + 2 * pad)
            side = c.get("side", "right")
            x0 = W - bw - 60 if side == "right" else 60
            y0 = 50
            d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh * pop), 22, fill=(252, 246, 232, 240), outline=(210, 196, 170, 255), width=3)
            if pop > 0.9:
                d.text((x0 + pad + 10, y0 + pad - 6), c["en"], font=big, fill=(52, 44, 40))
                d.text((x0 + pad + 10, y0 + pad + big.size * 1.2), c["zh"], font=mid, fill=(196, 72, 50))
    for s in plan.get("subs", []):
        if s["t0"] <= t < s["t1"]:
            lines = [(s["en"], small), (s.get("zh", ""), small)]
            lines = [l for l in lines if l[0]]
            w = max(d.textlength(txt, font=f) for txt, f in lines) + 60
            h = len(lines) * small.size * 1.35 + 30
            x0, y0 = (W - w) / 2, H - h - 36
            d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 16, fill=(20, 22, 30, 170))
            for j, (txt, f) in enumerate(lines):
                tw = d.textlength(txt, font=f)
                d.text(((W - tw) / 2, y0 + 15 + j * small.size * 1.35), txt, font=f, fill=(255, 255, 255))


def render_frame(plan, shots, t, fonts, fps):
    W, H = plan["size"]
    shot = next((s for s in shots if s.s["t"] <= t < s.s["t1"]), shots[-1])
    s = shot.s
    u = (t - s["t"]) / max(s["t1"] - s["t"], 1e-3)
    cam = s.get("cam", {})
    k0, k1 = cam.get("push", [1.0, 1.04])
    zoom = lerp(k0, k1, ease(u))
    pan = lerp(*cam.get("pan", [0, 0]), ease(u))

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    bg = load_rgba(s["bg"])
    if bg.size != (W, H):
        bg = bg.resize((W, H), Image.LANCZOS)
    canvas.alpha_composite(bg)

    actors = []
    hs = hero_state(shot, t, fps)
    hs["who"] = "hero"
    actors.append(hs)
    for c in s.get("extras", []):  # companions and props with their own sheet or still image
        if not (c.get("t0", s["t"]) <= t < c.get("t1", s["t1"])):
            continue
        cu = ease((t - c.get("t0", s["t"])) / max(c.get("t1", s["t1"]) - c.get("t0", s["t"]), 1e-3))
        pts = c.get("path", [[c.get("x", W / 2), c.get("y", shot.lanes["mid"])]])
        seg = min(int(cu * (len(pts) - 1)), max(len(pts) - 2, 0))
        v = cu * (len(pts) - 1) - seg if len(pts) > 1 else 0
        x = lerp(pts[seg][0], pts[min(seg + 1, len(pts) - 1)][0], v)
        y = lerp(pts[seg][1], pts[min(seg + 1, len(pts) - 1)][1], v)
        bob = math.sin(t * 2 * math.pi / c.get("bob_period", 1.6)) * c.get("bob", 0) * H
        if c.get("attach") == "hero":
            x, y = hs["x"] + c.get("dx", 0) * hs["scale"], hs["y"]
            bob -= hs["lift"] + c.get("dy", 0) * hs["scale"]
        if "sheet" in c:
            tiles, anchors, ref_h = load_sheet(c["sheet"])
            kk = (int(t * fps) // 2) % len(tiles)
            img, anc = tiles[kk], anchors[kk]
            base = ref_h
        else:
            img = load_rgba(c["img"])
            anc, base = (img.width / 2, img.height), img.height
        sc = c.get("h", 0.15) * H / base * (shot.lane_scale(y) if c.get("lane_scale", True) else 1)
        actors.append(dict(x=x, y=y, lift=-bob, img=img, anchor=anc, scale=sc, flip=c.get("flip", False),
                           lane=c.get("lane", "mid"), who="extra", shadow=c.get("shadow", True)))

    def draw_actor(a):
        y_px = a["y"] * H
        if a.get("shadow", True) and a["lift"] < H * 0.5:
            shadow(canvas, a["x"], y_px, a["img"].width * a["scale"] * 0.45, a["lift"])
        paste_anchor(canvas, a["img"], a["anchor"], a["x"], y_px - a["lift"], a["scale"], a["flip"])

    ordered = sorted(actors, key=lambda a: a["y"])
    for a in ordered:
        if a["lane"] == "back":
            draw_actor(a)
    if s.get("mid_strip"):
        place_layer(canvas, s["mid_strip"], W, H, -pan * 0.5)
    for a in ordered:
        if a["lane"] != "back":
            draw_actor(a)
    if s.get("near_strip"):
        bobn = math.sin(t * 2 * math.pi / 2.2) * 4
        place_layer(canvas, s["near_strip"], W, H, -pan * 1.4 + bobn)

    canvas = grade(canvas, s.get("warm", 0))
    if zoom != 1.0 or pan:
        cw, ch = W / zoom, H / zoom
        cx = W / 2 + pan
        cy = H / 2 + (H - ch) / 2 * cam.get("anchor_low", 0.6)
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        canvas = canvas.resize((W, H), Image.LANCZOS, box=box)
    for tr in plan.get("fades", []):  # [{"t": 0, "d": 0.5, "dir": "in"}]
        if tr["t"] <= t < tr["t"] + tr["d"]:
            v = (t - tr["t"]) / tr["d"]
            a = 1 - v if tr.get("dir", "in") == "in" else v
            black = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * a)))
            canvas.alpha_composite(black)
    draw_text_layer(canvas, t, plan, fonts, W, H)
    return canvas.convert("RGB")


def main():
    global ROOT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timesheet")
    ap.add_argument("output")
    ap.add_argument("--stills", nargs="+", type=float, help="write PNG stills at these seconds instead of a video")
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float)
    ap.add_argument("--font")
    ap.add_argument("--root", default=".", help="project root (folder containing work/ and src/)")
    a = ap.parse_args()
    ROOT = Path(a.root)
    plan = json.load(open(a.timesheet))
    plan.setdefault("size", [1920, 1080])
    fps = plan.get("fps", 24)
    W, H = plan["size"]
    if os.path.exists(ROOT / "audio" / "subs.json") and "subs" not in plan:
        plan["subs"] = json.load(open(ROOT / "audio" / "subs.json"))
    shots = [Shot(s, W, H) for s in sorted(plan["shots"], key=lambda s: s["t"])]
    fp = font_path(a.font)
    fonts = (ImageFont.truetype(fp, 64), ImageFont.truetype(fp, 46), ImageFont.truetype(fp, 34))

    if a.stills:
        out = Path(a.output)
        out.mkdir(parents=True, exist_ok=True)
        for t in a.stills:
            render_frame(plan, shots, t, fonts, fps).save(out / f"still_{t:07.2f}.png")
            print("wrote", out / f"still_{t:07.2f}.png")
        return

    t1 = a.t1 if a.t1 is not None else plan["dur"]
    n = int(round((t1 - a.t0) * fps))
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.output], stdin=subprocess.PIPE)
    last = None
    for i in range(n):
        t = a.t0 + i / fps
        if i % 2 == 0 or last is None:  # every drawing is held for two frames
            last = render_frame(plan, shots, t, fonts, fps).tobytes()
        ff.stdin.write(last)
        if i % (fps * 5) == 0:
            print(f"\r{t:6.1f}/{t1:.1f}s", end="", flush=True)
    ff.stdin.close()
    if ff.wait():
        sys.exit("ffmpeg failed")
    print(f"\nwrote {a.output}")


if __name__ == "__main__":
    main()
