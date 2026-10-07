# Narration

## How the kit calls ElevenLabs

- `POST /v1/text-to-speech/{voice_id}/with-timestamps`: the response carries character-level start and end times, which drive both `until("phrase")` cues and the captions.
- `previous_text` / `next_text` carry the neighbouring sentences, so delivery flows across segment boundaries instead of every segment sounding like a fresh start. Set `"context": false` in `video.json` to turn it off.
- A fixed `seed` keeps re-synthesis close to the earlier take.
- Output is `mp3_44100_128`. Higher bitrates need a higher subscription tier; set `voice.output_format` only if the account supports it.

## Choosing a voice

- **Audition before committing.** `python -m kit audition ID1 ID2 ID3` renders `voice.audition_text` (put the hardest names and numbers of the script in it) once per voice into `build/audition/`. Let the user listen; a Whisper transcript of each tells you whether the names survive.
- Settings that suited calm explainers: stability 0.55, similarity 0.75, style 0.1, speaker boost on, speed 1.0, on `eleven_multilingual_v2`.
- **Stock voices** (`python -m kit voices`) are licensed for this use.
- **Cloned voices** (`python -m kit voices --mine`) are for the account owner's own voice, or a voice they have consent to use. Never clone or imitate a real presenter, including the creator of the style you are borrowing.
- Different voices pace differently: swapping voices on the same script can change its length by 10% or more. A new voice means re-running `audio`, `render` and `assemble`, which re-time every scene.

## Cost and credits

- `python -m kit narrate --dry-run` prints how many characters will be billed. Show it to the user before a large run.
- Credits can run out mid-run. Segments already synthesized are cached; finish layout on `draft` audio, report exactly what is blocked, and resume `narrate` once credits are topped up. Never present a draft-audio build as the finished video.
- The cache (`~/.cache/explainer-video/tts`, or `$EXPLAINER_TTS_CACHE`) is keyed on voice, model, settings, seed, text, and neighbouring text. When only a neighbour changed, the earlier take is reused ("reused (context differs)"); pass `--strict-context` to pay for a fresh take.

## Key handling

- The key lives only in the process environment. Run through the user's secret manager so it never lands in shell history, a file, or the transcript.
- Some keys are scoped: a missing `models_read` permission blocks `/v1/models`, and a missing `pronunciation_dictionaries_write` blocks server-side dictionaries. The kit needs neither: pick the model from current ElevenLabs docs, and pronunciation aliases are applied locally.
- Error bodies are scrubbed of the key before they are raised; keep it that way in any code you add.

## Pronunciation

- Aliases in `pronunciations.json` are whole-word, case-sensitive replacements applied to spoken text before synthesis.
- Whisper cannot judge an invented name: a product name spoken correctly can still transcribe as unrelated words. For names, listen to the segment rather than trusting the word-match score.
- Unusual unit names blur into common ones even when spelled out. Prefer words the audience says out loud when precision isn't the point.
