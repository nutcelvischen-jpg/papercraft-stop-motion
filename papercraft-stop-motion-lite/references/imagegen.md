# ImageGen asset prompts

Use one prompt per distinct subject. Pass the approved master (and turnaround) as visual reference in every later asset call. For transparent assets, request real transparent pixels in tool settings and in the prompt. Never let ImageGen draw text, labels or logos.

## Master puppet

> One original full-body cartoon [species]. [Silhouette, posture, proportions, distinguishing shapes, matte cardstock palette, one identifiable accessory, facing direction.] Layer the puppet from hand-cut matte dyed cardstock, with subtly irregular edges, shallow contact shadows between paper pieces and tactile fibers. Neutral stance, readable silhouette, generous clear margin all around, no ground, no text. Transparent outside the silhouette and through true gaps between parts.

## Turnaround (required for depth paths)

> Reference image 1 is the exact puppet. Draw it four times in one row, fixed order: front, front three-quarter, profile facing right, back. Same scale, feet on one baseline, clear gutters, transparent canvas, no text.

## Action sheet

> Reference image 1 is the exact identity and paper construction of [character]; reference image 2 is its turnaround. Keep colors, eye shape, limb count, proportions, accessory shape and scale. Draw [2 rows × 4 columns for an eight-pose action, or 2 × 2 for a close-up or four poses], one complete pose per equal cell with clear gutters. Row-major order: [pose 1 … pose 8 with view per pose, e.g. "crouch (¾), push off (¾), airborne rising (profile), peak tuck (profile), falling (profile), impact squash (¾), recover (¾), stand (front)"]. Grounded feet share a baseline. No location, no object other than any named held prop, no crop, labels or guides. Transparent canvas.

Plan one sheet per verb family from the timesheet. Include view changes inside sheets so the hero can walk toward and away from camera: `walk_toward` (front poses), `walk_away` (back poses), `turn_around` (front → ¾ → profile → back), `jump_onto`, `climb`, `sit_lie`, `carry`, `give_receive`, plus close-up emotion sheets (wonder, joy, sad, relief).

For a held prop, pass the character and the exact prop as references, name the limb, and record a hand pivot per tile. For continuity, compare tiles at final scale and keep facing and scale constant inside a sheet.

## Backgrounds and depth strips

> Front-facing eye-level papercraft lightbox inside a visible paper frame; glowing fiber on sliced edges, soft shadows between layers, [palette and mood light], [shot size and landmarks]. A receding staging floor with three readable depths (far, middle, near). Thin nearest foreground because a separate cut-paper strip will be placed in front. Fill the canvas. Omit these, they are composited later: [hero, companions, movable objects].

Make a different backplate for each location and for each close view of a location (wide, medium, close or low angle). Generate transparent mid and near strips against the wide reference: upper region empty, extra width for parallax. A mid strip with a gap lets the hero walk "behind" it in the back lane.

## Props and effects

- Interactive prop sheet: 1 × N states (closed/open, upright/tipped, empty/full), each isolated on transparent canvas, same scale.
- Effect sheet: 2 × 4 cells of individual drops, splashes, leaves, sparkles or dust puffs, each a clear silhouette. Apply alpha and motion in compositing.

## Slicing

```sh
python3 scripts/split_sheet.py src/fox_jump_onto.png work/fox_jump_onto --rows 2 --cols 4 \
  --names crouch push rise peak fall impact recover stand
python3 scripts/split_sheet.py src/whale.png work/whale --rows 2 --cols 2 --float \
  --names swim1 swim2 rise smile
```

Use the reported foot-base anchor (or body-center anchor with `--float`) as a start. For jumps, carrying and riding, record explicit ankle, torso or hand pivots. Reject tiles whose solid alpha touches their cell boundary. Inspect for fragments, hidden overlap and joined poses.
