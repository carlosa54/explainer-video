"""Checks on the finished video: decode, loudness, intelligibility and caption timing.

Speech checks need faster-whisper (`pip install faster-whisper`); the model downloads on first use.
"""

import difflib
import json
import re
import statistics
import subprocess

from . import project as P

NUM = dict(zip("0123456789", "zero one two three four five six seven eight nine".split()))


def _words(text: str) -> list:
    text = text.lower().replace("-", " ").replace("+", " plus ")
    text = re.sub(r"\d", lambda m: f" {NUM[m.group()]} ", text)
    return re.sub(r"[^a-z ]", " ", text).split()


def _pcm(path):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-map", "0:a", "-f", "s16le", "-ac", "1",
                          "-ar", "16000", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def _whisper():
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("speech checks need faster-whisper: pip install faster-whisper") from None
    return WhisperModel("small.en", device="cpu", compute_type="int8")


def check_media(out):
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(out), "-f", "null", "-"], check=True)
    stats = subprocess.run(["ffmpeg", "-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", stats)[-1]
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", stats)[-1]
    print(f"decode ok; loudness {lufs} LUFS, true peak {peak} dBFS")


def check_speech(model, prompt):
    """Transcribe each segment and compare it with its caption: catches mispronounced names and garbled takes."""
    results, hit, total = {}, 0, 0
    for sid, caption, _spoken in P.segments():
        segments, _ = model.transcribe(_pcm(P.AUDIO / f"{sid}.wav"), beam_size=5, initial_prompt=prompt)
        heard = " ".join(s.text.strip() for s in segments)
        ref, hyp = _words(caption), _words(heard)
        matched = sum(b.size for b in difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False).get_matching_blocks())
        hit, total = hit + matched, total + len(ref)
        results[sid] = {"accuracy": round(matched / len(ref), 3), "heard": heard}
        flag = "" if matched / len(ref) >= 0.9 else "  <-- listen"
        print(f"{sid:12} {matched / len(ref):.2f}{flag}  {heard}")
    (P.BUILD / "speech_check.json").write_text(json.dumps(results, indent=2))
    print(f"word match {hit / total:.3f} ({hit}/{total})")


def check_captions(model, out, srt):
    """Compare each caption's first word with where Whisper hears it in the final video."""
    segments, _ = model.transcribe(_pcm(out), word_timestamps=True)
    heard = [(w.start, re.sub(r"[^a-z0-9]", "", w.word.lower())) for s in segments for w in s.words]
    offsets, misses = [], 0
    for block in srt.read_text().strip().split("\n\n"):
        lines = block.split("\n")
        start = lines[1].split(" --> ")[0]
        h, m, rest = start.split(":")
        t = int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))
        first = re.sub(r"[^a-z0-9]", "", lines[2].split()[0].lower())
        near = [ws for ws, w in heard if w == first and abs(ws - t) < 3]
        if not near:
            misses += 1
            continue
        best = min(near, key=lambda ws: abs(ws - t))
        offsets.append(t - best)
        if abs(t - best) > 0.6:
            print(f"  cue at {t:.2f}s off by {t - best:+.2f}s: {lines[2]!r}")
    if offsets:
        absd = sorted(abs(o) for o in offsets)
        print(f"captions matched {len(offsets)}, unmatched {misses}; median {statistics.median(absd):.2f}s, "
              f"max {absd[-1]:.2f}s")


def cmd_verify(args):
    """Decode + loudness always; add --speech for Whisper intelligibility and caption timing."""
    cfg = P.config()
    suffix = "-preview" if "--low" in args else ""
    out, srt = P.OUT / f"{cfg['name']}{suffix}.mp4", P.OUT / f"{cfg['name']}{suffix}.srt"
    check_media(out)
    if "--speech" in args:
        model = _whisper()
        check_speech(model, cfg["whisper_prompt"])
        check_captions(model, out, srt)
