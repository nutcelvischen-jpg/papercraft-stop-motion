---
name: papercraft-stop-motion
description: Create original cut-paper cartoon puppets, transparent character and action sheets, layered pop-up storybook environments, and multi-shot papercraft stop-motion shorts (30 s to 3 min) using built-in ImageGen and deterministic compositing. Use for 剪紙角色、紙藝動畫、紙雕定格、紙藝立體書, papercraft animal casts, or bilingual vocabulary story shorts in a papercraft series.
---

# Papercraft Stop Motion

Work in the user's language (Traditional Chinese for Taiwan when writing Chinese). Make character masters immediately when the brief already specifies the subjects and medium. When asked for a film, turn the supplied story, runtime or vocabulary into a timed **story, shot list and action timesheet**, lint it, then build. Proceed with sensible defaults for reversible choices.

**Tools.** `scripts/render.py`, `scripts/mix_audio.py` and `scripts/check_video.py` turn `work/timesheet.json` and `work/sound.json` into a checked MP4 ([references/timesheet-format.md](references/timesheet-format.md)). Use them as the default pipeline and extend them when a shot needs more; [references/runbook.md](references/runbook.md) is the step-by-step version.

The quality bar is a *story film*, not a vocabulary slideshow. A film fails review if any of these are true:

- One background and one camera for the whole film, or no cuts.
- The hero stays on one horizontal ground line, at one scale, for most of the film.
- The hero keeps the same pose (or a two-pose loop) for more than 2 s.
- Objects only pop in and stack up; nothing is picked up, carried, opened, ridden, climbed or handed over.
- There is no problem, setback, low point or turn — only a list of words.

## 1. Plan the film before any image

1. **Story arc.** Write a logline, then setup → want → try 1 → helper → try 2 → setback → low point (short score silence) → turn → payoff → final hold. Each vocabulary word must be *caused by* or *cause* a story event.
2. **Shots.** Budget about one shot per 6–10 s (≥ 12 shots for 2 min, ≥ 4 for 30 s). Mix wide, medium and close-up; every same-place cut changes view and scale by ≥ 1.5×. Use ≥ 1 new background per scene and ≥ 4 for 2 min. Close-ups carry emotion (wonder, joy, sad, relief).
3. **Action timesheet.** Read [references/staging.md](references/staging.md). Every shot lists timed action beats, each with a pose sheet, a depth lane and a path. Targets for 2 min: ≥ 48 action beats, ≥ 16 distinct action sheets, all 3 depth lanes, ≥ 8 vertical or depth actions (jump onto, climb, sit, lie, crouch, toward/away from camera, ride, fly/float, fall and recover). Scale 30 s films proportionally (≥ 12 beats, ≥ 6 sheets).
4. **Lint the plan.** `python3 scripts/plan_lint.py work/timesheet.json` must print `OK` before any costly generation. Fix the plan, not the threshold.

## 2. Design the paper world

- Cut, dyed matte cardstock with visible cut edges, quiet grain, shallow relief and small shadows between layers. Treat each piece as a rigid hinged element. Stage against a front-facing layered paper **lightbox with a visible frame and depth**: back sky, far set, mid set, staging floor that recedes, near strip.
- Light with intent: warm focal light on the hero and the key object, cooler surround; change the grade per story beat (setback cooler and darker, payoff warmer). Use bright pastels for lessons and cool stacked tones with warm focal light for bedtime stories, but never a flat, evenly lit poster.
- Give each original character a stable silhouette, distinct identifiers, fixed colors and a neutral pose. Record them in a cast manifest. Add a companion (bird, small friend) who reacts in most shots. For the original five-animal series, read [references/cast.md](references/cast.md).

## 3. Generate the artwork

Use built-in ImageGen. Read [references/imagegen.md](references/imagegen.md) for prompt blocks.

- One master per character, then a turnaround (front, ¾, profile, back) because depth paths need back and ¾ views.
- One action sheet per verb family in the timesheet (8 poses for full-body actions, 4 for close-ups), with pose lists from [references/pose-library.md](references/pose-library.md). Do not reuse a walk sheet to fake other actions.
- Separate generations for each background, each depth strip, each prop and each effect sheet. Props that the hero interacts with get their own state sheets (closed/open, empty/full, upright/tipped).
- Check alpha and silhouette, slice with `scripts/split_sheet.py`, keep `sheet.json` anchors, inspect tiles over light and dark. Reject clipped limbs, merged poses, palette drift, stray fragments.

## 4. Make it move

`scripts/render.py` implements everything below from the timesheet; extend it only if a shot needs something it cannot express.

1. **Depth staging.** Each shot defines three ground lines (back, mid, front). The hero's scale follows its ground y (`scale = s_mid * (y / y_mid) ** 1.6` is a good start) and its draw order follows lane. Paths are eased splines, not flat x-tweens; a walk toward camera grows, a walk away uses back/¾ poses and shrinks.
2. **Pose replacement on twos.** 24 fps, two frames per drawing. Change action beat at least every 2.5 s; inside a beat, cycle its poses. Use anticipation → action → impact → settle for every jump, landing, pick-up and reaction. Never stretch one pose into a hold > 2 s; idle holds still blink, breathe or move ears/tail.
3. **Interaction.** Attach props to a hand/mouth pivot recorded per pose; hand objects over between characters; let props change state on contact. Contact shadows follow the lane.
4. **Camera and transitions.** Gentle eased pushes ≤ 1.1×, pans that reveal, parallax with near strips moving most. Use hard cuts by default and 2–3 motivated paper transitions (layer slide, page turn, glow mix). Opening pop-up, closing hold ≥ 2 s.
5. **Vocabulary.** Show the English + Traditional Chinese card when the object or action is on screen and visible; voice the narration line, pause, then the word twice. Keep key shapes clear of the card and the subtitle plate. Bilingual subtitles on one plate, one row per language.
6. **Sound.** Separate stems: quiet score with sections per story beat and one silence at the low point; paper foley synced to every contact (steps, flaps, pops, splashes); narration from the requested voice provider. Mix with `scripts/mix_audio.py`. If the provider is unavailable, use an authorized local voice and disclose it.

**Secrets.** Read API keys only from environment variables or a secret file outside the project (e.g. `~/.config/papercraft/.env`). Never write a key into prompts, JSON, scripts, logs, `production-log.md` or the repository. Before any `git add`, run `python3 scripts/scan_secrets.py .`.

## 5. Check and deliver

Read [references/production.md](references/production.md) for the 2-minute template, the 30-second template and the full check list. Minimum: `plan_lint.py` OK, `check_video.py` all PASS, liveness (no quiet span > 2 s), hero size per shot size, contact sheet review of every shot, cut review, −14 LUFS / ≤ −1 dBTP, ffprobe duration, H.264 yuv420p + AAC, faststart. Write `production-log.md` with plan, image log, fixes and a self-rating naming the weakest shot.

Workflow inspiration: [lemo-animi](https://github.com/lemomo-ai/lemo-animi), specifically its Papercraft material, pose-sheet process and layered compositing.
