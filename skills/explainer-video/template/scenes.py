"""Scenes: one class per key in narration.SCENES, in the same order.

Each scene calls self.say(segment_id) for its segments, in order, and animates what
the narrator is saying. self.until("phrase") lines a change up with a spoken word.
"""

from kit.narrated import *  # noqa: F403


def node(label, color, w=2.2, h=1.0):
    return labeled(label, w, h, color, size=24)


def path_arrow(a, b, color=DIM):
    return Arrow(a.get_right(), b.get_left(), buff=0.15, stroke_width=4, color=color,
                 max_tip_length_to_length_ratio=0.12)


def layout():
    browser = node("Browser", INK).move_to(LEFT * 5.4 + UP * 0.6)
    lb = node("nginx", YELLOW).move_to(LEFT * 1.6 + UP * 0.6)
    apps = VGroup(*[node(f"app {i + 1}", BLUE, 1.7, 0.75) for i in range(3)]).arrange(DOWN, buff=0.3)
    apps.move_to(RIGHT * 1.9 + UP * 0.6)
    db = node("Postgres", GREEN, 2.2, 1.0).move_to(RIGHT * 5.3 + UP * 0.6)
    return browser, lb, apps, db


class Intro(Narrated):
    def construct(self):
        title = T("How a request reaches your app", 46, weight=BOLD).to_edge(UP, buff=0.8)
        bar = card(7.5, 0.8, INK, fill=0.05, radius=0.3).move_to(UP * 0.3)
        url = M("https://example.com", 28, SKY).move_to(bar)
        cursor = Rectangle(width=0.05, height=0.45, fill_color=INK, fill_opacity=1, stroke_width=0)

        self.say("intro_1")
        self.play(Write(title), run_time=1.0)
        self.play(Create(bar), run_time=0.5)
        self.play(AddTextLetterByLetter(url), run_time=1.0)
        cursor.next_to(url, RIGHT, buff=0.08)
        self.add(cursor)
        self.until("press enter")
        self.play(Indicate(bar, color=SKY, scale_factor=1.05), run_time=0.6)
        self.done(0.2)
        self.clear_all()


class Journey(Narrated):
    def construct(self):
        browser, lb, apps, db = layout()

        self.say("dns_1")
        self.play(FadeIn(browser, shift=RIGHT * 0.3), run_time=0.6)
        book = VGroup(card(2.6, 1.6, PURPLE, fill=0.08),
                      M("example.com", 18, PURPLE), M("→ 93.184.215.14", 18, INK)).move_to(LEFT * 3.5 + DOWN * 2.0)
        book[1:].arrange(DOWN, buff=0.15).move_to(book[0])
        dns_label = T("DNS", 22, PURPLE, BOLD).next_to(book[0], UP, buff=0.12)
        self.until("phone book")
        self.play(FadeIn(book, shift=UP * 0.3), FadeIn(dns_label), run_time=0.8)
        self.done()

        self.say("lb_1")
        a1 = path_arrow(browser, lb)
        self.play(FadeIn(lb, shift=LEFT * 0.3), GrowArrow(a1), FadeOut(book), FadeOut(dns_label), run_time=0.8)
        self.play(flash(a1, YELLOW), run_time=0.7)
        self.until("three app servers")
        self.play(LaggedStart(*[FadeIn(a, shift=LEFT * 0.3) for a in apps], lag_ratio=0.2), run_time=0.9)
        arrows = VGroup(*[Arrow(lb.get_right(), a.get_left(), buff=0.12, stroke_width=3, color=DIM) for a in apps])
        self.play(Create(arrows), run_time=0.5)
        busy = [check(GOOD).next_to(apps[1], RIGHT, buff=0.15)]
        self.until("free right now")
        self.play(arrows[1].animate.set_color(YELLOW), Indicate(apps[1], color=BLUE), FadeIn(*busy), run_time=0.8)
        self.done()

        self.say("db_1")
        a3 = path_arrow(apps[1], db)
        self.play(FadeIn(db, shift=LEFT * 0.3), GrowArrow(a3), FadeOut(*busy), run_time=0.8)
        self.play(flash(a3, GREEN), run_time=0.7)
        self.until("sends it back")
        back = [Line(a.get_end(), a.get_start()) for a in (a3, arrows[1], a1)]
        self.play(LaggedStart(*[flash(b, GOOD) for b in back], lag_ratio=0.5), run_time=1.2)
        self.done(0.3)
        self.clear_all()


class Outro(Narrated):
    def construct(self):
        browser, lb, apps, db = layout()
        whole = VGroup(browser, lb, apps, db).scale(0.8).move_to(UP * 0.4)
        self.say("outro_1")
        self.play(FadeIn(whole), run_time=0.8)
        stamp = T("≈ 40 ms", 64, YELLOW, BOLD).next_to(whole, DOWN, buff=0.6)
        self.until("forty")
        self.play(Write(stamp), run_time=0.8)
        self.done(1.0)
        self.clear_all()
