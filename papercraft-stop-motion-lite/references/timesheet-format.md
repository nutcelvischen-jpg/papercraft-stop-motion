# timesheet.json format (read by plan_lint.py and render.py)

All paths are relative to the project root. Times are seconds. `x` is pixels (0–1920), `y` is a fraction of frame height (0 top, 1 bottom). Characters in tiles face **right**; the renderer flips them when they move left.

## Top level

| Field | Required | Meaning |
| --- | --- | --- |
| `dur` | yes | Story length in seconds |
| `fps` | no | 24 (default). Drawings are held two frames each |
| `size` | no | `[1920, 1080]` |
| `cards` | no | `[{"t0","t1","en","zh","side":"right"|"left"}]` vocabulary cards |
| `subs` | no | `[{"t0","t1","en","zh"}]` subtitles; if absent, `audio/subs.json` is used |
| `fades` | no | `[{"t","d","dir":"in"|"out"}]` black fades |
| `shots` | yes | List of shots, back to back, covering 0 → `dur` |

## Shot

| Field | Required | Meaning |
| --- | --- | --- |
| `name`, `t`, `t1` | yes | Name and time span |
| `size` | yes | `wide`, `medium` or `close-up` (sets hero height 36 % / 48 % / 78 % at mid lane) |
| `bg` | yes | Backplate PNG |
| `mid_strip`, `near_strip` | no | Transparent strips. Back-lane actors are drawn **behind** the mid strip; the near strip is always in front and moves 1.4× the pan |
| `lanes` | no | Override `{"back":0.66,"mid":0.80,"front":0.93}` |
| `surfaces` | no | Raised levels, e.g. `{"rock":0.70,"boat":0.78}`; use as lane `"surface:rock"` |
| `hero_h` | no | Override hero height fraction |
| `cam` | no | `{"push":[1.0,1.05],"pan":[0,40]}`; keep push ≤ 1.1 |
| `warm` | no | −1 … 1 grade; −0.5 rain/setback, +0.5 payoff |
| `extras` | no | Companions, props, effects (below) |
| `beats` | yes | Hero action beats (below) |

## Beat (hero)

| Field | Meaning |
| --- | --- |
| `t` | Start time; the first beat starts at the shot start |
| `sheet` | Folder name in `work/tiles/` |
| `lane` | `back`, `mid`, `front` or `surface:<name>` |
| `path` | `[[x, y], …]` key points; `null` y means "this lane's ground". Omit to stand still where the last move ended (or at `x`) |
| `x` | Standing x when there is no path |
| `loop` | Cycle poses (default true when the sheet name contains walk/run/swim/fly/float/ride/idle) else play once across the beat |
| `arc`, `arc_h` | Jump arc (default on for jump/hop/leap sheets), height as fraction of H (0.15) |
| `flip` | Force facing left |
| `scale` | Extra scale factor |

## Extra (companion, prop or effect)

`{"sheet": "pigeon_fly"}` or `{"img": "src/prop_shell.png"}`, plus `t0`, `t1`, `x`, `y` or `path`, `h` (height fraction), `lane`, `bob` (fraction of H), `bob_period`, `flip`, `shadow`, `lane_scale`, and `"attach": "hero"` with `dx`, `dy` (pixels in tile space) to make the hero hold or carry it.

Start from `templates/timesheet_30s_weather.json`.
