# Production pattern

For any brief, establish a story with a want, a problem, a turn, a payoff and a final hold. Fit everything to the requested duration in the timesheet before generating costly variations. Every run of poses belongs to a shot with an anchor, a lane and a timed beat.

## Project layout

```
project/
  src/            approved masters, turnarounds, action sheets, backplates, depth strips, props, fx sheets
  work/           sliced tiles + sheet.json, timesheet.json, stills, contact sheets
  audio/          vo/*.wav + *.json (measured durations), stem_music, stem_foley, stem_vo, mix.wav, subs.json
  out/            deliverables only
  production-log.md
```

Track prompts and provenance per image. Keep credentials out of the project.

## Template: 2-minute bilingual story (7 words)

114 s story + 3 s title + 3 s end card = 120 s, 1368 drawings on twos.

| Part | Time | Shots | Story job | Required action types |
| --- | --- | --- | --- | --- |
| Setup | 0–15 s | wide → close-up | World, hero, companion; word 1 | walk in from back lane, turn, look up |
| Want | 15–31 s | medium → close-up | Discover the key object; word 2 | crouch, dig/pick up, hold up, joy jump |
| Try 1 | 31–42 s | wide | First attempt fails playfully; word 3 | run toward camera, get pushed back, shake off |
| Helper | 42–53 s | medium (side view) | New friend shows the way; word 4 | follow sideways, point, high-five |
| Try 2 | 53–73 s | wide, wide | Journey with a vehicle or tool; words 5–6 | climb onto, ride, look out, wave |
| Setback | 73–81 s | medium, tilt | Bigger obstacle | slide back, hold on, fall and recover |
| Low point | 81–87 s | close-up | Sad beat, 1–2 s score silence | droop, sit down, then ears lift |
| Turn | 87–103 s | wide, medium | Help arrives; word 7 | stand up, climb onto helper, ride |
| Payoff | 103–114 s | wide → close-up | Goal reached, recap | hop down, place object, hug, wave goodnight |

## Template: 30-second vocabulary lesson

Minimum 4 shots and ≥ 12 beats even for 30 s. Example for the weather lesson:

| Time | Shot | Word | Hero action (lane) |
| --- | --- | --- | --- |
| 0–2.3 | wide pop-up | — | Elephant walks in from back lane toward mid |
| 2.3–5.4 | wide | CLOUD 雲朵 | Stops, looks up, trunk points as cloud rolls in |
| 5.4–8.9 | medium | RAIN 下雨 | First drop hits trunk, shiver, crouch |
| 8.9–12.6 | medium | UMBRELLA 雨傘 | Reaches back, pulls umbrella out, opens it with a hinge snap |
| 12.6–16.1 | wide, low camera | PUDDLE 水窪 | Walks toward front lane, stops at puddle edge, peers in |
| 16.1–20.0 | close-up feet → medium | BOOTS 雨鞋 | Steps into boots one by one, anticipation crouch, big splash jump |
| 20.0–23.5 | wide | WIND 風 | Umbrella tugs, elephant slides back, holds on, spins |
| 23.5–28.5 | wide → close-up | RAINBOW 彩虹 | Umbrella closes, elephant climbs a hill (back lane), sits and gazes |
| 28.5–30 | hold | — | Close-up smile, blink, end card |

## Assets checklist (2 min)

- ≥ 4 backgrounds (wide, medium, close, plus one per extra location) and ≥ 2 depth strip layers.
- ≥ 16 hero action sheets + 3–4 close-up emotion sheets, ≥ 1 companion sheet, ≥ 1 effect sheet.
- One sheet per interactive prop with its states.

## Check and deliver

- `python3 scripts/plan_lint.py work/timesheet.json` → `OK` before generating; rerun after every plan change.
- Build with `scripts/render.py` → `scripts/mix_audio.py` → `scripts/check_video.py` (see runbook steps 9–10).
- Inspect every master alpha, every action sheet tile at final scale, and one still per beat. Make `work/contact.jpg` (one frame every 3 s) and `work/cuts.jpg` (frames either side of every cut).
- Liveness: per-second mean frame difference; flag spans > 2 s below 0.01 (normalized). Hero size: wide ≥ 33 % of frame height, medium ≥ 40 %, close-up ≥ 60 %.
- Sound: score, foley and narration are separate stems until the final mix; nonzero decoded audio; each narration region fits its measured duration; −14 LUFS, true peak ≤ −1 dBTP; a silence at the low point.
- `ffprobe -v error -show_streams -show_format output.mp4` and `ffmpeg -v error -i output.mp4 -f null -`: exact runtime, H.264 yuv420p, AAC, 1920×1080 or the requested size, `-movflags +faststart`.
- Check the first and last frames, every vocabulary beat with sound on, card/subtitle overlap with faces, foot slide, prop pivots.
- Write `production-log.md`: plan, image log with retries, review findings and fixes, must-pass verdicts, a 1–5 self-rating and the weakest shot.
- Provide the final MP4 and any requested assets. Preserve clip and narration timing if the voice is later replaced.
