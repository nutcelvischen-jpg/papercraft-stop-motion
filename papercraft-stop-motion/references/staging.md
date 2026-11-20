# Staging and action density

The difference between a flat paper slideshow and a living stop-motion film is *where* the puppet moves and *how often* it changes what it is doing.

## Depth lanes

Every shot defines three ground lines in frame pixels (1080p example for a wide shot):

| Lane | Ground y | Scale vs mid | Draw order | Use |
| --- | --- | --- | --- | --- |
| back | 0.66 H | ≈ 0.70× | behind mid set strip | Entrances from far away, companions, discoveries in the distance |
| mid | 0.80 H | 1.00× | main staging plane | Dialogue, vocabulary moments |
| front | 0.93 H | ≈ 1.30× | in front of mid strip, behind near strip | Arrivals toward camera, emotional beats, partial occlusion by near leaves |

- Scale from y: `s = s_mid * (y / y_mid) ** 1.6`; clamp to the size rule for the shot size.
- Changing lane is an action: walk toward camera (front pose → grows), walk away (back pose → shrinks), hop down a step, climb up a rock.
- Raised levels count as lanes too: a rock top, a boat deck, a whale's back, a branch, a cloud. Record each as `surface` with its own ground y and a contact shadow.
- Near strips occlude the hero at the front lane edges for at least part of the film; mid strips hide the hero's feet when walking in the back lane.

## Paths

- Describe movement as 2–4 key points with easing, e.g. `path: [[300,0.80],[820,0.86],[1180,0.93]]` in (x px, y as fraction of H). The renderer interpolates with a Catmull-Rom spline and derives scale and facing from the path.
- Arcs for jumps: anticipation crouch 4–6 drawings, airborne 6–10 drawings on an arc with peak ≥ 0.15 H, impact squash 2 drawings, settle 4 drawings. Add a dust or splash effect cell at impact.
- Keep the foot anchor on the path during walks; foot slide is a failure.

## Action vocabulary (choose many)

Locomotion: walk, run, tiptoe, sneak, hop, skip, jump up onto, hop down, climb, slide, swim, paddle, fly/float, ride, roll.
Body: sit, lie down, crouch, stretch, look up, look back over shoulder, turn around (front→¾→profile→back), spin, shake off water, shiver, yawn, sleep.
Hands/trunk/tail: reach, pick up, carry, hug, push, pull, open, close, point, wave, give, receive, catch, drop, dig, pat, high-five.
Emotion (close-up sheets): wonder, laugh, surprise, worry, sad droop, determination, relief, sleepy.

Each verb family needs its own action sheet; one sheet holds 8 full-body poses (or 4 close-up poses) of the same family.

## Density targets

| Runtime | Shots | Action beats | Distinct action sheets | Depth/vertical actions | Max same-pose hold |
| --- | --- | --- | --- | --- | --- |
| 30 s | ≥ 4 | ≥ 12 | ≥ 6 | ≥ 3 | 2 s |
| 60 s | ≥ 7 | ≥ 24 | ≥ 10 | ≥ 5 | 2 s |
| 120 s | ≥ 12 | ≥ 48 | ≥ 16 | ≥ 8 | 2 s |

A beat is a change of action sheet, a change of lane or surface, or a prop state change caused by the hero. Background motion (rain, waves) does not count.

## Timesheet format (`work/timesheet.json`)

```json
{
  "dur": 114.0,
  "fps": 24,
  "shots": [
    {
      "name": "s01_beach_arrival", "t": 0.0, "t1": 9.0, "size": "wide", "bg": "beach_wide",
      "lanes": {"back": 0.66, "mid": 0.80, "front": 0.93},
      "beats": [
        {"t": 0.0, "sheet": "fox_walk_back", "lane": "back", "path": [[1500,0.66],[1100,0.70]]},
        {"t": 2.2, "sheet": "fox_turn_around", "lane": "back"},
        {"t": 3.6, "sheet": "fox_run_toward", "lane": "front", "path": [[1100,0.70],[900,0.93]]},
        {"t": 6.0, "sheet": "fox_jump_onto", "lane": "surface:rock", "path": [[900,0.93],[1050,0.78]]},
        {"t": 7.6, "sheet": "fox_wave_hail", "lane": "surface:rock"}
      ]
    }
  ]
}
```

`plan_lint.py` reads this file. Keep it the single source of truth for render, foley cues and vocabulary card timing.
