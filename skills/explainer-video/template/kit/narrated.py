"""Manim base classes that keep animation in sync with narration.

    from kit.narrated import *

    class Intro(Narrated):
        def construct(self):
            self.say("intro_1")             # start segment audio now
            self.play(Write(title))         # animations that belong to it
            self.until("three parts")       # wait for the narrator to reach a phrase
            self.play(FadeIn(parts))
            self.done()                     # wait for the segment to finish

`say` waits for the previous segment (plus a short pause) to end before starting the
next one, so audio never overlaps and pictures never run ahead of the words. Each scene
writes build/timings/<Scene>.json, which `assemble` uses to place the narration track
and time the captions.
"""

import json

from manim import *  # noqa: F403

from . import project as P

CFG = P.config()
config.background_color = BG = "#0B0F17"
config.frame_width = 14.222  # 16:9 at Manim's default frame height of 8

FONT = CFG["font"]
MONO = CFG["mono_font"]
PAUSE = CFG["pause"]
CUE_LEAD = CFG["cue_lead"]

# A dark-ground palette: one hue per actor in the story, used consistently across scenes.
INK = "#E8ECF2"
DIM = "#6B7385"
FAINT = "#2A3142"
BLUE = "#58C4DD"
YELLOW = "#F2C14E"
GREEN = "#83C167"
ORANGE = "#FF8F5A"
PURPLE = "#B48EF0"
SKY = "#9CDCFE"
BAD = "#FC6255"
GOOD = "#7BD88F"

_DUR = json.loads((P.AUDIO / "durations.json").read_text()) if (P.AUDIO / "durations.json").exists() else {}
_ALIGN = json.loads((P.AUDIO / "alignment.json").read_text()) if (P.AUDIO / "alignment.json").exists() else {}


# ---------------------------------------------------------------- primitives

def T(text, size=28, color=INK, weight=NORMAL, font=None):
    return Text(text, font=font or FONT, font_size=size, color=color, weight=weight)


def M(text, size=22, color=INK):
    return Text(text, font=MONO, font_size=size, color=color)


def card(w, h, color, fill=0.10, radius=0.14, stroke=3):
    return RoundedRectangle(corner_radius=radius, width=w, height=h, stroke_color=color,
                            stroke_width=stroke, fill_color=color, fill_opacity=fill)


def labeled(label, w, h, color, size=24, fill=0.10):
    box = card(w, h, color, fill)
    text = T(label, size, color)
    if text.width > w - 0.3:
        text.scale_to_fit_width(w - 0.3)
    return VGroup(box, text.move_to(box))


def pill(label, color, size=20):
    text = T(label, size, color)
    box = RoundedRectangle(corner_radius=0.2, width=text.width + 0.45, height=max(0.46, text.height + 0.26),
                           stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=0.12)
    return VGroup(box, text.move_to(box))


def check(color=GOOD, scale=0.28, width=7):
    mark = VMobject(stroke_color=color, stroke_width=width)
    mark.set_points_as_corners([LEFT * 0.55 + UP * 0.05, DOWN * 0.45 + LEFT * 0.1, UP * 0.6 + RIGHT * 0.65])
    return mark.scale(scale)


def cross(color=BAD, scale=0.25, width=7):
    return VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(color, width).scale(scale)


def flash(mob, color, width=8, time_width=0.4, **kw):
    """A pulse of light travelling along a path: requests, signals, data moving."""
    return ShowPassingFlash(mob.copy().set_stroke(color, width), time_width=time_width, **kw)


# ---------------------------------------------------------------- narration-driven scene

class Narrated(MovingCameraScene):
    def setup(self):
        super().setup()
        self.segments = []
        self.segment_end = 0.0

    def say(self, seg_id):
        """Start a narration segment once the previous one (plus PAUSE) has finished."""
        if seg_id not in _DUR:
            raise ValueError(f"no audio for {seg_id!r}; run `python -m kit audio`")
        remaining = self.segment_end - self.renderer.time
        if remaining > 0.02:
            self.wait(remaining)
        start = self.renderer.time
        self.add_sound(str(P.AUDIO / f"{seg_id}.wav"))
        self.segments.append({"id": seg_id, "start": round(start, 3), "duration": _DUR[seg_id]})
        self.segment_end = start + _DUR[seg_id] + PAUSE

    def until(self, cue):
        """Wait until the narrator reaches a phrase (or a number of seconds) in the current segment.

        Phrases are matched against the spoken text after pronunciation aliases, so
        cue on the words as spoken ("eighteen", not "18").
        """
        seg = self.segments[-1]
        if isinstance(cue, str):
            align = _ALIGN[seg["id"]]
            at = align["text"].lower().find(P.aliased(cue).lower())
            if at < 0:
                raise ValueError(f"cue {cue!r} not found in {seg['id']}: {align['text']!r}")
            cue = max(0.0, align["starts"][at] - CUE_LEAD)
        target = seg["start"] + cue
        if target - self.renderer.time > 0.02:
            self.wait(target - self.renderer.time)

    def done(self, tail=0.0):
        """Wait for the current segment to finish (plus `tail` seconds)."""
        remaining = self.segment_end - self.renderer.time + tail
        if remaining > 0.02:
            self.wait(remaining)

    def clear_all(self, run_time=0.8):
        self.play(*[FadeOut(m) for m in self.mobjects if m is not self.camera.frame], run_time=run_time)

    def tear_down(self):
        P.TIMINGS.mkdir(parents=True, exist_ok=True)
        payload = {"scene": type(self).__name__, "segments": self.segments, "length": round(self.renderer.time, 3)}
        (P.TIMINGS / f"{type(self).__name__}.json").write_text(json.dumps(payload, indent=2))
        super().tear_down()


# ---------------------------------------------------------------- real screenshots

SHOT_WIDTH = 11.8  # scene units; leaves a margin and the caption band free


def shot(name, width=SHOT_WIDTH):
    """A screenshot from screens/, framed with a thin border. Boxes are given in the image's own pixels."""
    path = P.ROOT / "screens" / name
    img = ImageMobject(str(path))
    img.scale_to_fit_width(width).move_to(UP * 0.55)
    border = RoundedRectangle(corner_radius=0.08, width=img.width + 0.06, height=img.height + 0.06,
                              stroke_color="#3A4357", stroke_width=3).move_to(img)
    return Group(border, img)


def _box_points(sh, box):
    img = sh[1]
    s = img.width / img.pixel_array.shape[1]
    x0, y0, x1, y1 = box
    ul = img.get_corner(UL)
    return ul + RIGHT * x0 * s + DOWN * y0 * s, ul + RIGHT * x1 * s + DOWN * y1 * s


def spotlight(sh, box, color=YELLOW):
    """Dim the screenshot everywhere except `box` (x0, y0, x1, y1 in image pixels) and outline it."""
    img = sh[1]
    p0, p1 = _box_points(sh, box)
    hole = RoundedRectangle(corner_radius=0.05, width=p1[0] - p0[0] + 0.08, height=p0[1] - p1[1] + 0.08).move_to((p0 + p1) / 2)
    veil = Rectangle(width=img.width, height=img.height).move_to(img)
    dim = Difference(veil, hole, stroke_width=0, fill_color=BG, fill_opacity=0.62)
    outline = hole.copy().set_fill(opacity=0).set_stroke(color, 4)
    return VGroup(dim, outline)


def framing(sh, box, zoom=1.0):
    """Camera center and width that show `box` comfortably, above the caption band, without leaving the screenshot."""
    fw = config.frame_width
    p0, p1 = _box_points(sh, box)
    bw, bh = p1[0] - p0[0], p0[1] - p1[1]
    width = min(max(bw * 1.35, bh * 1.35 * 16 / 9 * 1.25, 4.2) / zoom, fw)
    height = width * 9 / 16
    center = (p0 + p1) / 2 + DOWN * height * 0.04
    img = sh[1]
    if width < img.width:
        center[0] = min(max(center[0], img.get_left()[0] + width / 2), img.get_right()[0] - width / 2)
    if height < img.height:
        center[1] = min(center[1], img.get_top()[1] - height / 2)
        center[1] = max(center[1], img.get_bottom()[1] + height / 2 - height * 0.12)
    return center, width


class ScreenScene(Narrated):
    """Pan, zoom and spotlight over real screenshots."""

    def show_shot(self, name, run_time=0.9):
        sh = shot(name)
        self.play(FadeIn(sh, scale=0.94), self.camera.frame.animate.move_to(ORIGIN).set(width=config.frame_width),
                  run_time=run_time)
        return sh

    def look(self, sh, box, color=YELLOW, zoom=1.0, run_time=0.9, spot=None):
        """Move the camera to `box` and spotlight it; pass the previous spotlight as `spot` to morph it."""
        center, width = framing(sh, box, zoom)
        new = spotlight(sh, box, color)
        anims = [self.camera.frame.animate.move_to(center).set(width=width)]
        anims.append(FadeIn(new) if spot is None else ReplacementTransform(spot, new))
        self.play(*anims, run_time=run_time)
        return new

    def wide(self, run_time=0.8, spot=None):
        anims = [self.camera.frame.animate.move_to(ORIGIN).set(width=config.frame_width)]
        if spot is not None:
            anims.append(FadeOut(spot))
        self.play(*anims, run_time=run_time)

    def callout(self, text, anchor, color=YELLOW, direction=RIGHT, size=24):
        """A label sized for the current zoom, on a solid backing so it reads over busy screens."""
        scale = self.camera.frame.width / config.frame_width
        label = T(text, size, color, BOLD).scale(scale)
        bg = BackgroundRectangle(label, color=BG, fill_opacity=0.85, buff=0.12 * scale)
        return VGroup(bg, label).next_to(anchor, direction, buff=0.2 * scale)

    def swap(self, old, name, run_time=0.9):
        new = shot(name)
        self.play(FadeOut(old, shift=LEFT * 0.6), FadeIn(new, shift=LEFT * 0.6),
                  self.camera.frame.animate.move_to(ORIGIN).set(width=config.frame_width), run_time=run_time)
        return new
