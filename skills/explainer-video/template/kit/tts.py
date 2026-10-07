"""ElevenLabs narration: voice listing, auditions, cached synthesis with timestamps, and draft audio.

The API key is read from ELEVENLABS_API_KEY in the process environment only. It is
never printed, logged, written to disk or put on a command line, and it is scrubbed
from any error text before that text is raised.

Synthesized segments are cached by content in EXPLAINER_TTS_CACHE (default
~/.cache/explainer-video/tts), so a second cut of the same video, or a re-run after
a script edit, only pays for sentences whose text or voice actually changed.
"""

import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import project as P

API = "https://api.elevenlabs.io"
CACHE = Path(os.environ.get("EXPLAINER_TTS_CACHE", Path.home() / ".cache" / "explainer-video" / "tts"))


# ---------------------------------------------------------------- HTTP

def _key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key:
        raise SystemExit("ELEVENLABS_API_KEY is not set. Export it, or run through your secret manager "
                         "(e.g. `op run -- python -m kit narrate`). Use `python -m kit draft` for free placeholder audio.")
    return key


def _scrub(text: str) -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    return text.replace(key, "[REDACTED]") if key else text


def request(method: str, path: str, body=None, query: str = "", retries: int = 3):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(f"{API}{path}{query}", data=data, method=method)
        req.add_header("xi-api-key", _key())
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read()), resp.headers.get("request-id")
        except urllib.error.HTTPError as err:
            detail = _scrub(err.read().decode(errors="replace"))[:600]
            if err.code in (429, 500, 502, 503) and attempt + 1 < retries:
                time.sleep(4 * (attempt + 1))
                continue
            raise SystemExit(f"ElevenLabs {method} {path} failed: HTTP {err.code}: {detail}") from None
        except urllib.error.URLError as err:
            if attempt + 1 < retries:
                time.sleep(4)
                continue
            raise SystemExit(f"ElevenLabs {method} {path} network error: {_scrub(str(err.reason))}") from None


def tts(voice: dict, text: str, extra: dict):
    body = {"text": text, "model_id": voice["model_id"], "voice_settings": voice["settings"], **extra}
    fmt = voice.get("output_format", "mp3_44100_128")
    data, rid = request("POST", f"/v1/text-to-speech/{voice['voice_id']}/with-timestamps", body,
                        query=f"?output_format={fmt}")
    return base64.b64decode(data["audio_base64"]), data, rid


# ---------------------------------------------------------------- commands

def cmd_voices(args):
    """List voices. Default: stock (premade) voices; --mine: your own and cloned voices."""
    category = "" if "--mine" in args else "&category=premade"
    out, token = [], None
    while True:
        q = f"?page_size=100{category}" + (f"&next_page_token={token}" if token else "")
        data, _ = request("GET", "/v2/voices", query=q)
        for v in data.get("voices", []):
            if "--mine" in args and v.get("category") == "premade":
                continue
            labels = v.get("labels") or {}
            out.append(v)
            print(v["voice_id"], "|", v.get("name"), "|", v.get("category"), "|", labels.get("gender"),
                  labels.get("age"), labels.get("accent"), "|", labels.get("descriptive") or labels.get("use_case") or "")
        if not data.get("has_more"):
            break
        token = data.get("next_page_token")
    P.BUILD.mkdir(parents=True, exist_ok=True)
    (P.BUILD / "voices.json").write_text(json.dumps(out, indent=2))


def cmd_audition(args):
    """Synthesize the same hard sentence once per VOICE_ID[:MODEL_ID] into build/audition/."""
    voice = P.config()["voice"]
    text = P.aliased(voice.get("audition_text") or P.segments()[0][2])
    folder = P.BUILD / "audition"
    folder.mkdir(parents=True, exist_ok=True)
    if not args:
        raise SystemExit("usage: python -m kit audition VOICE_ID[:MODEL_ID] ...")
    for arg in args:
        vid, _, model = arg.partition(":")
        v = {**voice, "voice_id": vid, "model_id": model or voice["model_id"]}
        target = folder / f"{vid}-{v['model_id']}.mp3"
        if target.exists():
            print("cached", target)
            continue
        audio, _, _ = tts(v, text, {"seed": voice.get("seed", 7)})
        target.write_bytes(audio)
        print("wrote", target)


def _requests(cfg):
    """The exact request for every segment: (segment_id, text, extra, full_key, text_key)."""
    voice = cfg["voice"]
    flat = [(sid, P.aliased(spoken)) for sid, _caption, spoken in P.segments()]
    base = [voice["voice_id"], voice["model_id"], voice["settings"], voice.get("seed", 7)]
    out = []
    for i, (sid, text) in enumerate(flat):
        extra = {"seed": voice.get("seed", 7)}
        if voice.get("context", True):
            if i > 0:
                extra["previous_text"] = flat[i - 1][1]
            if i + 1 < len(flat):
                extra["next_text"] = flat[i + 1][1]
        full = hashlib.sha256(json.dumps([*base, text, extra.get("previous_text"), extra.get("next_text")],
                                         sort_keys=True).encode()).hexdigest()[:20]
        loose = hashlib.sha256(json.dumps([*base, text], sort_keys=True).encode()).hexdigest()[:20]
        out.append((sid, text, extra, full, loose))
    return out


def _install(sid, src_mp3: Path, meta: dict):
    P.SEGMENTS.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_mp3, P.SEGMENTS / f"{sid}.mp3")
    (P.SEGMENTS / f"{sid}.json").write_text(json.dumps(meta))


def _current(sid):
    meta = P.SEGMENTS / f"{sid}.json"
    return json.loads(meta.read_text()) if meta.exists() else {}


def _from_cache(sid, full, loose, strict=False, dry=False) -> bool:
    """Install real audio for a segment from the cache if any exists; True when the segment is covered."""
    if _current(sid).get("cache_key") == full:
        return True
    hit = CACHE / f"{full}.mp3"
    if not hit.exists() and not strict and (CACHE / f"loose-{loose}.json").exists():
        hit = CACHE / f"{json.loads((CACHE / f'loose-{loose}.json').read_text())['key']}.mp3"
    if not hit.exists():
        return False
    if not dry:
        _install(sid, hit, {**json.loads(hit.with_suffix(".json").read_text()), "cache_key": full})
    print("cached" if hit.stem == full else "reused (context differs)", sid)
    return True


def cmd_narrate(args):
    """Synthesize every segment that is not already cached. --dry-run prints the cost without calling the API.
    --strict-context re-synthesizes when only the neighbouring sentences changed."""
    cfg = P.config()
    dry, strict = "--dry-run" in args, "--strict-context" in args
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = []
    for sid, text, extra, full, loose in _requests(cfg):
        if not _from_cache(sid, full, loose, strict, dry):
            todo.append((sid, text, extra, full, loose))
    chars = sum(len(t) for _, t, *_ in todo)
    print(f"{len(todo)} segments to synthesize, {chars} characters")
    if dry or not todo:
        return
    for sid, text, extra, full, loose in todo:
        audio, data, rid = tts(cfg["voice"], text, extra)
        meta = {"request_id": rid, "text": text, "voice_id": cfg["voice"]["voice_id"],
                "alignment": data.get("alignment"), "normalized_alignment": data.get("normalized_alignment")}
        (CACHE / f"{full}.mp3").write_bytes(audio)
        (CACHE / f"{full}.json").write_text(json.dumps(meta))
        (CACHE / f"loose-{loose}.json").write_text(json.dumps({"key": full}))
        _install(sid, CACHE / f"{full}.mp3", {**meta, "cache_key": full})
        print("synthesized", sid, f"{len(text)} chars")
    print("narration complete")


def cmd_draft(args):
    """Free placeholder narration for layout work: macOS `say`, or espeak-ng elsewhere.

    Character timings are spread evenly, and every segment is marked provisional so
    `assemble` refuses a final build until `narrate` has replaced it. Segments with real
    audio in the cache use that instead.
    """
    voice = P.config()["voice"]
    P.SEGMENTS.mkdir(parents=True, exist_ok=True)
    say = shutil.which("say")
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if not (say or espeak):
        raise SystemExit("draft audio needs macOS `say` or espeak-ng")
    for sid, text, _extra, full, loose in _requests(P.config()):
        cur = _current(sid)
        if (cur.get("provisional") and cur.get("text") == text) or _from_cache(sid, full, loose):
            continue
        tmp = P.SEGMENTS / f"{sid}.draft.{'aiff' if say else 'wav'}"
        if say:
            subprocess.run(["say", "-v", voice.get("draft_voice", "Samantha"), "-r", "165", "-o", str(tmp), text], check=True)
        else:
            subprocess.run([espeak, "-s", "160", "-w", str(tmp), text], check=True)
        mp3 = P.SEGMENTS / f"{sid}.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-ar", "44100", str(mp3)], check=True)
        tmp.unlink()
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                             "-of", "default=nw=1:nk=1", str(mp3)]))
        n = len(text)
        starts = [0.1 + (dur - 0.3) * i / n for i in range(n)]
        ends = [0.1 + (dur - 0.3) * (i + 1) / n for i in range(n)]
        (P.SEGMENTS / f"{sid}.json").write_text(json.dumps({"provisional": True, "text": text, "alignment": {
            "characters": list(text), "character_start_times_seconds": starts, "character_end_times_seconds": ends}}))
        print("draft", sid, f"{dur:.1f}s")


if __name__ == "__main__":
    sys.exit("run through `python -m kit`")
