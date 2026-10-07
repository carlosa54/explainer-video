"""The script. Scene names must match the classes in scenes.py, in playback order.

Each segment is (id, caption) or (id, caption, spoken):
  caption  what viewers read on screen, numbers and symbols as digits
  spoken   what the voice receives, numbers spelled out the way they should be said
Both must contain the same sentences in the same order: captions are timed sentence by
sentence from the spoken audio. Brand names that the voice mispronounces go in
pronunciations.json instead, so the caption keeps the real spelling.
"""

SCENES = {
    "Intro": [
        ("intro_1",
         "You type an address and press enter. Here is what happens next."),
    ],
    "Journey": [
        ("dns_1",
         "First, DNS turns the name into an address, like looking up a number in a phone book."),
        ("lb_1",
         "The request reaches nginx, which picks one of 3 app servers that is free right now.",
         "The request reaches nginx, which picks one of three app servers that is free right now."),
        ("db_1",
         "That server asks Postgres for your data, builds the page, and sends it back."),
    ],
    "Outro": [
        ("outro_1",
         "All of that, in about 40 milliseconds.",
         "All of that, in about forty milliseconds."),
    ],
}
