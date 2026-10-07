# Animation

## The narration clock

`from kit.narrated import *` gives Manim plus the kit's helpers. Each scene class subclasses `Narrated` (diagrams) or `ScreenScene` (screenshots) and is named exactly like its key in `narration.SCENES`.

- `self.say("id")` starts that segment's audio once the previous one (plus `pause` from `video.json`) has ended. Everything played after it belongs to it.
- `self.until("phrase")` waits until the narrator starts that phrase, minus `cue_lead` (0.12 s), so the picture lands with the word. Match the **spoken** text after aliases: cue on `"eighteen"`, not `"18"`. A missing phrase raises with the segment's text.
- `self.until(2.5)` waits until 2.5 s into the current segment.
- `self.done(tail)` waits for the segment to finish. End each scene with `done` then `clear_all()`.
- If the animations after a `say` take longer than its audio, the next `say` simply starts later and `python -m kit timing` reports the silent gap. Shorten the animations, or move some under the next segment.

Each render writes `build/timings/<Scene>.json`; `assemble` places the narration track and captions from those, so the picture and sound cannot drift.

## Visual craft

- **Motion carries meaning.** Transform one shape into the next, move the camera to what is being explained, send a `flash` along a path for a request or signal, count with growing grids. A slide deck with a few blinking dots is the failure mode.
- **One hue per actor**, kept for the whole film (the palette constants in `narrated.py`: `BLUE`, `YELLOW`, `GREEN`, `ORANGE`, `PURPLE`, …). A viewer should know which machine a shape belongs to by colour alone.
- **Progressive reveal.** Introduce each element as it is named, not all at once.
- **Diagrams for structure, screens for proof.** Draw how parts connect; show a real screenshot when the point is "this exists and works".
- **Boundaries are claims.** If two systems are separate, draw them apart; nesting one box inside another says it runs inside it.

## Layout rules from frame review

- Keep the bottom band (below about y = -2.6) clear: captions are burned in there.
- Titles need room from the top edge, and labels need room from each other; overlapping labels were the most common defect found in frame review.
- `flash` a plain `Line`, not an `Arrow` copy: rotated arrow copies leave tip fragments mid-flash.
- Fonts come from `video.json` (`font`, `mono_font`). The defaults are Avenir Next and Menlo on macOS and DejaVu elsewhere; Pango silently substitutes a missing font, so check the first frames.

## Screens

`ScreenScene` works over PNGs in `screens/`. Boxes are `(x0, y0, x1, y1)` in the screenshot's own pixels: read them off the image.

```python
class Dashboard(ScreenScene):
    def construct(self):
        self.say("dash_1")
        sh = self.show_shot("dashboard.png")               # fade in, camera wide
        self.until("This panel")
        spot = self.look(sh, (500, 250, 1800, 700))       # zoom + dim everything else
        spot = self.look(sh, (500, 800, 1800, 1200), spot=spot)  # morph to the next box
        note = self.callout("free capacity", spot[1], GREEN, DOWN)
        self.play(FadeIn(note))
        self.done()
        self.wide(spot=spot)
        sh = self.swap(sh, "next.png")                   # slide to the next screenshot
```

- `look` frames the box above the caption band and clamps the camera to the screenshot, so no empty margins show.
- Place callouts over quiet parts of the screen: the backing is translucent, and text underneath shows through.
- A spotlight on a box touching the top edge of the screenshot crowds the frame; pick a box with some margin, or zoom less (`zoom=0.8`).

## Rendering

- `python -m kit render --low` renders 480p15 in parallel, about four times faster than full resolution. Name scenes to render only those: `python -m kit render --low Dashboard`.
- Logs go to `build/logs/<Scene>.log`. Manim's stdin is closed, so a wrong scene name fails at once instead of waiting at Manim's scene picker.
- `python -m kit build --low --draft` gives a full watermarked preview before any narration is paid for.
