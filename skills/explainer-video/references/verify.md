# Verification

Run `python -m kit verify --speech` on the final build, then review frames. Fix and rebuild until each check passes or its exception is written into the result.

| Check | How | Pass |
| --- | --- | --- |
| Decode | `verify` decodes every stream | no errors |
| Loudness | `verify` measures EBU R128 | about −16 LUFS integrated, true peak ≤ −1 dBFS |
| Intelligibility | `verify --speech`: Whisper transcribes each segment and compares it with its caption | ≥ 95% word match overall; listen to every segment flagged `<-- listen` (below 90%) |
| Caption timing | `verify --speech`: Whisper word times in the final MP4 against each cue's first word | median ≤ 0.1 s, max ≤ 0.7 s; explain any outlier (Whisper often mistimes the word after a pause) |
| Pacing | `python -m kit timing` | no silent gap reported mid-scene |
| Length | final duration | within the brief's target |
| Removed content | `grep -niE 'term1\|term2' narration.py scenes.py out/*.srt` for everything the brief said to cut | no matches, in narration or on-screen text |
| Frames | the contact sheet, then full-resolution frames from every scene and every screenshot spotlight | no overlapping labels, nothing under the caption band, no empty stage, camera never past a screenshot's edge |
| Secrets | `grep -rn` the project, `build/` and `out/` for the key's prefix; look at every screenshot | nothing found |
| Draft audio | `assemble` without `--draft` succeeds | it refuses while any segment is a draft |

To check frames, pull single frames at times from the timestamped script in `out/`:

```sh
ffmpeg -v error -ss 74.5 -i out/NAME.mp4 -frames:v 1 frame-74.png
```

Whisper scores names it doesn't know as misses (an invented product name heard as two ordinary words). A low score on a name is a cue to listen, not proof of a mispronunciation.
