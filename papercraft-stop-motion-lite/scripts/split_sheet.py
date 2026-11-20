#!/usr/bin/env python3
"""Slice transparent ImageGen sheets and preserve trim metadata for anchor alignment."""
import argparse
import json
import re
from pathlib import Path

from PIL import Image


def split_sheet(source: Path, out: Path, rows: int, cols: int, names: list[str], floating: bool = False) -> list[dict]:
    with Image.open(source) as image:
        alpha = image.convert("RGBA")
    if alpha.getchannel("A").getextrema()[0] == 255:
        raise ValueError("The sheet must have actual transparency.")
    width, height = alpha.size
    tiles = []
    for i, name in enumerate(names):
        y, x = divmod(i, cols)
        left, top = x * width // cols, y * height // rows
        right, bottom = (x + 1) * width // cols, (y + 1) * height // rows
        cell = alpha.crop((left, top, right, bottom))
        mask = cell.getchannel("A")
        trim = mask.point(lambda value: 255 if value >= 128 else 0).getbbox()
        if trim is None:
            raise ValueError(f"{name}: empty cell")
        a, b, c, d = trim
        if min(a, b, cell.width - c, cell.height - d) < 3:
            raise ValueError(f"{name}: artwork touches a cell boundary")
        cell.putalpha(mask.point(lambda value: 0 if value < 24 else value))
        # Foot-base anchor for grounded poses; body-center anchor for swimmers, flyers and floating props.
        anchor = ((c - a) / 2 + 2, (d - b) / 2 + 2) if floating else ((c - a) / 2 + 2, d - b + 2)
        tiles.append((name, cell.crop((a - 2, b - 2, c + 2, d + 2)), [left + a, top + b, left + c, top + d], anchor))

    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, image, bounds, anchor in tiles:
        file = name + ".png"
        image.save(out / file)
        manifest.append({"file": file, "source_bounds": bounds, "anchor_kind": "center" if floating else "base", "base_anchor": anchor})
    (out / "sheet.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--names", nargs="+", required=True)
    parser.add_argument("--float", dest="floating", action="store_true", help="use a body-center anchor instead of the foot base")
    args = parser.parse_args()
    if min(args.rows, args.cols) < 1 or len(args.names) != args.rows * args.cols:
        parser.error("Provide a positive grid and one tile name per cell in row-major order.")
    if len(set(args.names)) != len(args.names) or any(not re.fullmatch("[a-z0-9_-]+", n) for n in args.names):
        parser.error("Use distinct lowercase ASCII tile names.")
    try:
        split_sheet(args.source, args.output, args.rows, args.cols, args.names, args.floating)
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
