"""A one-minute tour of the explainer-video repository, made with the skill itself."""

SCENES = {
    "Intro": [
        ("intro_1",
         "This is explainer-video: a skill that lets an agent make narrated, animated explainers. This video was made with it.",
         "This is explainer video: a skill that lets an agent make narrated, animated explainers. This video was made with it."),
    ],
    "Pipeline": [
        ("pipe_1",
         "You describe the topic. The agent writes the script with you, animates it on free draft audio, and only then pays for the real voice."),
        ("pipe_2",
         "Then it renders every scene with Manim, and checks the result."),
    ],
    "Sync": [
        ("sync_1",
         "The voice returns a timestamp for every character. So when I say now, the picture moves."),
        ("sync_2",
         "The same timestamps cut the captions, so they land on the words too."),
    ],
    "Cuts": [
        ("cuts_1",
         "Every new cut is its own folder, so earlier versions stay intact. Sentences are cached by their text, so a shorter edit only pays for what changed."),
    ],
    "Verify": [
        ("verify_1",
         "Before delivery, the kit checks decoding, loudness and caption timing, and Whisper listens to every sentence."),
    ],
    "Outro": [
        ("outro_1",
         "Clone the repo, link the skill, and ask your agent for a video."),
    ],
}
