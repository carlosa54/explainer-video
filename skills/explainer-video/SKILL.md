---
name: explainer-video
description: Make narrated, animated explainer videos (3Blue1Brown-style Manim diagrams, real app screenshots, ElevenLabs voice, synced captions). Use when asked to create an explainer or walkthrough video, re-cut or shorten an existing one, or change its narration voice.
---

# Explainer video

A finished explainer is an MP4 whose pictures move with the words: each animation starts when the narrator reaches the phrase it illustrates, and captions are timed from the voice's own character timestamps. The work is a pipeline in a **project** folder: `narration.py` (the script), `scenes.py` (Manim scenes), `video.json` (title, voice), `screens/` (screenshots), and `kit/` (the vendored toolkit, run as `python -m kit <command>` from the project root).

Every **cut** (a new version, a shortened edit, a new voice) is a new project folder made with `scripts/new_project.py DEST --from OLD`. Earlier cuts stay playable and untouched; synthesized sentences are cached by content outside the project, so a cut only pays for sentences that changed.

The key comes from `ELEVENLABS_API_KEY` in the environment. Run voice commands through whatever secret manager the user has (`op run --`, `av inject +ELEVENLABS_API_KEY --`, a plain `export`); never print, log, or write the key.

## Steps

### 1. Facts sheet

Collect what the video may claim, from the user's brief, their repos and configs, and questions to them. Write each claim as **verified** (seen in config, a screen, or the user's words) or **illustrative** (a placeholder, an example, a conceptual layout). Pin the audience, the target length, and what must be cut.

Done when every on-screen or spoken claim you plan to make traces to a verified line, and the illustrative ones are listed for the result notes. Read [`references/script.md`](references/script.md) for the claims that most often go wrong.

### 2. Project

`python3 <skill>/scripts/new_project.py DEST` for a new video, or `--from OLD` for a new cut. Install `template/requirements.txt` into a venv (Manim needs Cairo, Pango and ffmpeg on the system). Set `name`, `title` and `voice` in `video.json`.

Done when `python -m kit draft && python -m kit build --low` builds the bundled example (or the copied cut) into `out/`.

### 3. Script

Write `narration.py`: scenes in playback order, each a list of `(id, caption, spoken)` segments, one to three sentences each. Budget about 150 spoken words per minute of video; let the real audio decide the final length rather than speeding the voice. Put pronunciations of names in `pronunciations.json`.

Show the user the script as a table (scene, narration, what's on screen) and ask the questions only they can answer. Done when the user has approved the wording: synthesis costs credits, script edits before it are free.

### 4. Animate on draft audio

`python -m kit draft` makes free placeholder narration with even character timings, so you can lay out scenes before paying for the voice. Write one `Narrated` (diagrams) or `ScreenScene` (screenshots) class per scene in `scenes.py`, driving every change with `say` / `until` / `done`. Iterate with `python -m kit build --low` and look at frames.

Done when every segment has a picture that changes with its words, `python -m kit timing` reports no silent gaps, and no frame in the low preview has overlapping text or an empty stage. Read [`references/animation.md`](references/animation.md) before writing scenes; read [`references/screens.md`](references/screens.md) before capturing any live app.

### 5. Voice

If no voice is chosen, audition: `python -m kit voices`, then `python -m kit audition ID1 ID2 ID3` on a sentence full of the hard names, and let the user pick by ear. Then `python -m kit narrate --dry-run` to see the character cost, and `python -m kit narrate`.

Done when `narrate` reports 0 segments left to synthesize. Read [`references/narration.md`](references/narration.md) for voice settings, cloned voices, credits and key permissions.

### 6. Build and verify

`python -m kit build` (full resolution), then `python -m kit verify --speech`. Review the contact sheet in `out/` and full-resolution frames from every scene, and fix what you find. A new voice changes the pacing, so a voice swap always means a full re-render, never a soundtrack replacement.

Done when every check in [`references/verify.md`](references/verify.md) passes or its exception is explained.

### 7. Deliver

Report the absolute paths of the MP4, SRT, script and contact sheet; duration; voice and model; the verification numbers; the illustrative or unverified list from step 1; and the rebuild commands. Never call draft audio finished narration: `assemble` refuses a final build while any segment is still a draft.
