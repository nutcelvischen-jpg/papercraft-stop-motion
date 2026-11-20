---
name: papercraft-stop-motion-lite
description: Step-by-step papercraft stop-motion film maker for smaller models. Writes JSON and image prompts only; bundled scripts render, mix and check the video. Use for 紙藝定格動畫、剪紙角色、兒童雙語單字故事短片 when the model should follow a fixed procedure.
---

# Papercraft Stop Motion (Lite)

Reply in the user's language. For Chinese, use Traditional Chinese with Taiwan wording.

## The only way to work

1. Open [references/runbook.md](references/runbook.md) and do Steps 1 → 10 in order.
2. Do not skip a step. Do not continue until the step's **Gate** passes.
3. If one gate fails 3 times, stop and tell the user what failed.
4. You write only: the story box, `work/timesheet.json`, `work/sound.json`, `work/assets.md`, image prompts, `production-log.md`.
5. You never write compositing, animation or audio-mixing code. Run the scripts instead:

| Need | Command |
| --- | --- |
| Check the plan | `python3 scripts/plan_lint.py work/timesheet.json` |
| Slice an action sheet | `python3 scripts/split_sheet.py src/X.png work/tiles/X --rows 2 --cols 4 --names p1 p2 p3 p4 p5 p6 p7 p8` |
| Still images | `python3 scripts/render.py work/timesheet.json work/stills --stills 1 6 12` |
| Silent video | `python3 scripts/render.py work/timesheet.json out/silent.mp4` |
| Add sound | `python3 scripts/mix_audio.py work/sound.json out/silent.mp4 out/final.mp4` |
| Final check | `python3 scripts/check_video.py out/final.mp4 --dur 30 --contact work/contact.jpg` |
| Before git | `python3 scripts/scan_secrets.py .` |

## Copy, don't invent

- Timesheet: copy `templates/timesheet_30s_weather.json`, then edit. Fields: [references/timesheet-format.md](references/timesheet-format.md).
- Action poses: copy lists from [references/pose-library.md](references/pose-library.md).
- Image prompts: copy blocks from [references/imagegen.md](references/imagegen.md) and fill the brackets.
- Characters: use [references/cast.md](references/cast.md) when the hero is one of the five series animals.

## Numbers to hit

| Film length | Shots | Beats (action changes) | Different action sheets | Max time in one beat |
| --- | --- | --- | --- | --- |
| 30 s | 4–8 | 12+ | 6+ | 2.5 s |
| 60 s | 7–10 | 24+ | 10+ | 2.5 s |
| 120 s | 12–16 | 48+ | 16+ | 2.5 s |

Use lanes `back`, `mid` and `front` and at least one `surface:` (rock, hill, boat). `plan_lint.py` checks all of this.

## Never

- Never put an API key in any file, prompt, JSON, log or commit. Read keys from environment variables only.
- Never let image generation draw text, labels or logos. Words come from `cards` and `subs` in the JSON.
- Never use one background for the whole film, or keep the hero in one pose for more than 2.5 s.
- Never draw a copyrighted character.
