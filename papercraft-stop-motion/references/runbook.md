# Runbook: fixed steps for any model

Follow the steps in order. Do not write your own compositing or audio code: edit JSON and run the scripts. Each step has a gate; do not continue until the gate passes. If a gate fails 3 times, stop and report what failed.

Project root layout: `src/` (generated images), `work/` (tiles, timesheet, stills), `audio/`, `out/`.

## Step 1 — Story (no tools)

Copy and fill this, one line per box:

```
Title:            Hero:            Companion:            Place(s):
Want (what the hero wants):
Words (EN / 繁中), in story order:
Setup  →  Want  →  Try 1 (fails)  →  Helper  →  Try 2  →  Setback  →  Low point  →  Turn  →  Payoff  →  Goodnight hold
```

Gate: every word is attached to one box; there is a setback and a turn.

## Step 2 — Timesheet

Copy `templates/timesheet_30s_weather.json` to `work/timesheet.json`. Change names, times, words, sheets and backgrounds. Keep the structure. Pick sheets from `references/pose-library.md`.

Rules: shots are 3–10 s; beats are ≤ 2.5 s; use all three lanes; use at least one `surface:`; each word card starts when its object or action is visible.

Gate: `python3 scripts/plan_lint.py work/timesheet.json` prints `OK`.

## Step 3 — List the images

Write `work/assets.md` with one line per file the timesheet references: every `bg`, strip, `sheet` and `img`. Mark each as `master`, `sheet 2x4`, `sheet 2x2`, `bg`, `strip` or `prop`.

Gate: every name in the timesheet appears once in `work/assets.md`.

## Step 4 — Character master and turnaround

Generate the master with the prompt in `references/imagegen.md`, then the turnaround. Save `src/<hero>.png`, `src/<hero>_turn.png`.

Gate: open the image. Transparent background; whole body visible; colours match the cast entry.

## Step 5 — Action sheets

For each sheet in `work/assets.md`: use the action-sheet prompt, paste the pose list from the pose library, pass the master and turnaround as references. Save `src/<sheet>.png`. Slice:

```sh
python3 scripts/split_sheet.py src/<sheet>.png work/tiles/<sheet> --rows 2 --cols 4 --names p1 p2 p3 p4 p5 p6 p7 p8
```

Use `--rows 2 --cols 2 --names p1 p2 p3 p4` for 2×2 sheets and add `--float` for flying or swimming.

Gate: the script exits without error, and the tiles look like the same character. If a tile touches its border or the colours drift, regenerate that sheet (max 2 retries).

## Step 6 — Backgrounds, strips, props, effects

Generate each with the prompts in `references/imagegen.md`. Backgrounds must be 1920×1080 with no characters and no text. Strips and props must be transparent. Slice effect sheets like action sheets.

Gate: `python3 scripts/render.py work/timesheet.json work/stills --stills <one time per shot>` runs without "missing image", and you have opened every still.

## Step 7 — Fix stills

Look at every still and fix in the JSON only:

| Problem | JSON fix |
| --- | --- |
| Hero too small or too big | shot `hero_h`, or beat `scale` |
| Feet floating / sunk | `lanes` or `surfaces` values |
| Hero hidden by card or subtitles | beat `x` / path, or card `side` |
| Hero behind a strip when it should be in front | beat `lane` |
| Scene too flat or dark | `warm`, `cam.push` |

Gate: re-rendered stills look right.

## Step 8 — Voice, foley, music

Write narration lines into `work/sound.json` (`vo` list) and the same text into `subs`. Generate each line as `audio/vo/L<n>.wav` with the requested voice provider (key from the environment only, see SECURITY in README). Add foley on every landing, splash, open, pick-up. Add a quiet score with one `silence` at the low point.

Gate: `python3 scripts/mix_audio.py ...` reports no FAIL (no overlaps, nothing after the end).

## Step 9 — Render and mix

```sh
python3 scripts/render.py work/timesheet.json out/silent.mp4
python3 scripts/mix_audio.py work/sound.json out/silent.mp4 out/final.mp4
```

## Step 10 — Check

```sh
python3 scripts/check_video.py out/final.mp4 --dur <seconds> --contact work/contact.jpg
```

Gate: all PASS, and you opened `work/contact.jpg`. Then write `production-log.md` (story, shots, retries, fixes, weakest shot) and deliver `out/final.mp4`.
