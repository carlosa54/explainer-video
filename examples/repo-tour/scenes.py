"""Scenes for the repository tour. Each class matches a key in narration.SCENES."""

import random

from kit.narrated import *  # noqa: F403

STEPS = [("Script", SKY), ("Draft audio", DIM), ("Voice", PURPLE), ("Render", BLUE), ("Verify", GREEN)]


def film_frame(w=5.2, h=2.9):
    frame = card(w, h, INK, fill=0.04, radius=0.18)
    play = Triangle(fill_color=YELLOW, fill_opacity=0.9, stroke_width=0).rotate(-PI / 2).scale(0.42).move_to(frame)
    holes = VGroup(*[RoundedRectangle(corner_radius=0.03, width=0.22, height=0.14, stroke_width=0, fill_color=INK,
                                      fill_opacity=0.35) for _ in range(9)]).arrange(RIGHT, buff=0.32)
    top = holes.copy().next_to(frame.get_top(), DOWN, buff=0.14)
    bottom = holes.copy().next_to(frame.get_bottom(), UP, buff=0.14)
    return VGroup(frame, play, top, bottom)


def waveform(n=64, width=10.5, seed=3):
    rng = random.Random(seed)
    bars = VGroup(*[Rectangle(width=width / n * 0.55, height=0.15 + 1.1 * rng.random() ** 1.6, stroke_width=0,
                              fill_color=PURPLE, fill_opacity=0.75) for _ in range(n)])
    return bars.arrange(RIGHT, buff=width / n * 0.45, aligned_edge=ORIGIN)


def folder(label, color):
    body = card(2.3, 1.5, color, fill=0.10, radius=0.1)
    tab = RoundedRectangle(corner_radius=0.06, width=0.9, height=0.3, stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=0.25).next_to(body.get_corner(UL), UR, buff=0).shift(DOWN * 0.08 + RIGHT * 0.15)
    return VGroup(tab, body, T(label, 22, color).move_to(body))


def sentences(colors, w=1.8):
    rows = VGroup(*[RoundedRectangle(corner_radius=0.05, width=w * (0.65 + 0.35 * ((i * 7) % 5) / 4), height=0.16,
                                     stroke_width=0, fill_color=c, fill_opacity=0.85) for i, c in enumerate(colors)])
    return rows.arrange(DOWN, buff=0.12, aligned_edge=LEFT)


def dim(box):
    box[0].set_stroke(opacity=0.3).set_fill(opacity=0.03)
    box[1].set_opacity(0.3)


def lit(box):
    """Bring a dimmed labeled box back to its normal look."""
    return AnimationGroup(box[0].animate.set_stroke(opacity=1).set_fill(opacity=0.18), box[1].animate.set_opacity(1))


class Intro(Narrated):
    def construct(self):
        name = M("explainer-video", 64, INK).move_to(UP * 1.9)
        tagline = T("narrated, animated explainers, made by an agent", 28, DIM).next_to(name, DOWN, buff=0.3)
        film = film_frame().move_to(DOWN * 1.0)

        self.say("intro_1")
        self.play(AddTextLetterByLetter(name), run_time=1.0)
        self.until("narrated")
        self.play(FadeIn(tagline, shift=UP * 0.2), run_time=0.7)
        self.play(DrawBorderThenFill(film), run_time=1.0)
        self.until("This video")
        loop = Circle(radius=0.75, stroke_color=YELLOW, stroke_width=5).move_to(film[1])
        self.play(Create(loop), film[1].animate.scale(1.15), run_time=0.8)
        self.play(Rotate(loop, angle=TAU, about_point=loop.get_center()), run_time=1.0)
        self.done(0.2)
        self.clear_all()


class Pipeline(Narrated):
    def construct(self):
        boxes = VGroup(*[labeled(text, 2.15, 0.95, color, size=22) for text, color in STEPS]).arrange(RIGHT, buff=0.5)
        boxes.move_to(UP * 0.6)
        arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), buff=0.06, stroke_width=3, color=FAINT,
                                max_tip_length_to_length_ratio=0.3) for a, b in zip(boxes, boxes[1:])])
        you = VGroup(T("you", 24, INK, BOLD), T("describe the topic", 20, DIM)).arrange(DOWN, buff=0.1)
        you.next_to(boxes[0], UP, buff=0.9)
        free = pill("free", GOOD, 18).next_to(boxes[1], DOWN, buff=0.25)
        paid = pill("paid, once", YELLOW, 18).next_to(boxes[2], DOWN, buff=0.25)
        for b in boxes:
            dim(b)

        self.say("pipe_1")
        self.play(FadeIn(you, shift=DOWN * 0.2), run_time=0.6)
        self.play(FadeIn(boxes), Create(arrows), run_time=0.8)
        self.until("writes the script")
        self.play(lit(boxes[0]), GrowArrow(Arrow(you.get_bottom(), boxes[0].get_top(), buff=0.1,
                                                                    color=SKY, stroke_width=3)), run_time=0.6)
        self.until("free draft audio")
        self.play(lit(boxes[1]), flash(arrows[0], SKY), FadeIn(free, shift=UP * 0.15), run_time=0.7)
        self.until("real voice")
        self.play(lit(boxes[2]), flash(arrows[1], PURPLE), FadeIn(paid, shift=UP * 0.15), run_time=0.7)
        self.done()

        self.say("pipe_2")
        self.until("renders")
        self.play(lit(boxes[3]), flash(arrows[2], BLUE), run_time=0.7)
        frames = VGroup(*[card(0.5, 0.3, BLUE, fill=0.3, radius=0.04) for _ in range(5)]).arrange(RIGHT, buff=0.08)
        frames.next_to(boxes[3], DOWN, buff=0.3)
        self.play(LaggedStart(*[FadeIn(f, shift=LEFT * 0.2) for f in frames], lag_ratio=0.2), run_time=0.8)
        self.until("checks")
        tick = check(GOOD, 0.35).next_to(boxes[4], DOWN, buff=0.3)
        self.play(lit(boxes[4]), flash(arrows[3], GREEN), Create(tick), run_time=0.7)
        self.done(0.3)
        self.clear_all()


class Sync(Narrated):
    def construct(self):
        code = VGroup(M('self.say("sync_1")', 24, INK), M('self.until("now")', 24, YELLOW),
                      M("self.play(Flash(dot))", 24, INK)).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        panel = card(code.width + 0.7, code.height + 0.5, FAINT, fill=0.35, radius=0.12)
        code_box = VGroup(panel, code.move_to(panel)).move_to(UP * 2.2 + LEFT * 3.2)
        wave = waveform().move_to(DOWN * 0.1)
        sentence = "The voice returns a timestamp for every character."
        line = T(sentence, 28, DIM).next_to(wave, DOWN, buff=0.45)
        words, spans, pos = sentence.split(), [], 0
        for w in words:  # Text drops spaces from its glyphs, so index words by their non-space characters
            spans.append((pos, pos + len(w)))
            pos += len(w)
        dot = Dot(radius=0.22, color=YELLOW).move_to(UP * 2.2 + RIGHT * 3.6)

        self.say("sync_1")
        self.play(FadeIn(code_box, shift=RIGHT * 0.2), FadeIn(wave), FadeIn(line), run_time=0.8)
        for word, (a, b) in zip(words, spans):
            self.until(word.strip(".").lower() if word != "a" else " a ")
            self.play(line[a:b].animate.set_color(INK), run_time=0.12)
        self.until("now")
        head = Line(wave.get_top() + UP * 0.2, wave.get_bottom() + DOWN * 0.2, stroke_color=YELLOW, stroke_width=4)
        head.move_to(wave.get_center() + RIGHT * 3.0)
        self.play(FadeIn(head), Indicate(code[1], color=YELLOW, scale_factor=1.08), FadeIn(dot, scale=0.3), run_time=0.35)
        self.play(Flash(dot, color=YELLOW, line_length=0.4, num_lines=12, flash_radius=0.45), run_time=0.6)
        self.done()

        self.say("sync_2")
        screen = card(6.4, 3.0, INK, fill=0.04, radius=0.12).move_to(DOWN * 0.3)
        cap_bar = RoundedRectangle(corner_radius=0.05, width=4.4, height=0.45, stroke_width=0, fill_color=BG,
                                   fill_opacity=0.9).move_to(screen.get_bottom() + UP * 0.45)
        cap = T("they land on the words too", 20, INK).move_to(cap_bar)
        self.play(FadeOut(code_box), FadeOut(dot), FadeOut(head), FadeOut(line),
                  wave.animate.scale(0.5).next_to(screen, UP, buff=0.35), FadeIn(screen), run_time=0.8)
        self.until("land on")
        self.play(FadeIn(cap_bar), FadeIn(cap, shift=UP * 0.1), run_time=0.4)
        self.done(0.3)
        self.clear_all()


class Cuts(Narrated):
    def construct(self):
        cuts = VGroup(folder("first cut", BLUE), folder("shorter", ORANGE), folder("new voice", PURPLE))
        cuts.arrange(RIGHT, buff=1.0).move_to(UP * 1.6)
        cache = VGroup(card(2.6, 1.6, GREEN, fill=0.08, radius=0.14), T("cache", 22, GREEN, BOLD))
        cache[1].next_to(cache[0].get_top(), DOWN, buff=0.15)
        cache.move_to(DOWN * 1.2 + LEFT * 2.6)
        api = VGroup(card(2.6, 1.6, YELLOW, fill=0.08, radius=0.14), T("synthesize", 22, YELLOW, BOLD))
        api[1].next_to(api[0].get_top(), DOWN, buff=0.15)
        api.move_to(DOWN * 1.2 + RIGHT * 2.6)

        self.say("cuts_1")
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.3) for c in cuts], lag_ratio=0.3), run_time=1.2)
        self.until("stay intact")
        self.play(*[Indicate(c[1], color=c[2].color, scale_factor=1.05) for c in cuts], run_time=0.7)
        self.until("cached")
        self.play(FadeIn(cache), FadeIn(api), run_time=0.6)
        rows = sentences([INK] * 6).next_to(cuts[1], DOWN, buff=0.15).scale(0.8)
        self.play(FadeIn(rows), run_time=0.4)
        self.until("only pays")
        changed = {1, 4}
        moves = []
        for i, r in enumerate(rows):
            target = api if i in changed else cache
            color = YELLOW if i in changed else GREEN
            moves.append(r.animate.set_fill(color).move_to(target[0].get_center() + DOWN * 0.15 + UP * (0.25 - 0.18 * (i % 4))))
        self.play(LaggedStart(*moves, lag_ratio=0.12), run_time=1.6)
        self.done(0.3)
        self.clear_all()


class Verify(Narrated):
    def construct(self):
        items = [("decoding", "decoding"), ("loudness", "loudness"), ("caption timing", "caption timing"),
                 ("every sentence heard by Whisper", "listens")]
        rows = VGroup(*[VGroup(Square(0.42, stroke_color=DIM, stroke_width=3), T(label, 30, INK)).arrange(RIGHT, buff=0.35)
                        for label, _ in items]).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to(UP * 0.4)
        self.say("verify_1")
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in rows], lag_ratio=0.15), run_time=0.9)
        for row, (_, cue) in zip(rows, items):
            self.until(cue)
            tick = check(GOOD, 0.32).move_to(row[0])
            self.play(Create(tick), row[0].animate.set_stroke(GOOD), run_time=0.4)
        self.done(0.4)
        self.clear_all()


class Outro(Narrated):
    def construct(self):
        cmds = VGroup(M("git clone …/explainer-video", 26, INK),
                      M("ln -s …/skills/explainer-video ~/.claude/skills/", 26, INK)).arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        prompt = T("“Make a two-minute explainer of how our deploys work.”", 30, YELLOW)
        group = VGroup(cmds, prompt).arrange(DOWN, buff=0.7).move_to(UP * 0.4)
        self.say("outro_1")
        self.until("Clone")
        self.play(FadeIn(cmds[0], shift=UP * 0.2), run_time=0.5)
        self.until("link")
        self.play(FadeIn(cmds[1], shift=UP * 0.2), run_time=0.5)
        self.until("ask")
        self.play(Write(prompt), run_time=1.2)
        self.done(1.2)
        self.play(FadeOut(group), run_time=0.8)
