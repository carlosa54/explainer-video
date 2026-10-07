"""Turn segment MP3s into trimmed WAVs, durations and character alignment for the scenes."""

import json
import subprocess

from . import project as P


def probe_duration(path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "default=nw=1:nk=1", str(path)]))


def cmd_audio(args):
    """Write build/audio/<id>.wav, durations.json and alignment.json.

    Audio is never sped up. Trailing silence past 0.25 s after the last spoken character
    is trimmed; leading audio is kept so the alignment times stay valid.
    """
    P.AUDIO.mkdir(parents=True, exist_ok=True)
    durations, alignment, drafts = {}, {}, []
    for sid, _caption, spoken in P.segments():
        meta_path = P.SEGMENTS / f"{sid}.json"
        if not meta_path.exists():
            raise SystemExit(f"no audio for {sid}; run `python -m kit narrate` (or `draft`)")
        meta = json.loads(meta_path.read_text())
        if meta["text"] != P.aliased(spoken):
            raise SystemExit(f"{sid}: script changed since its audio was made; run `python -m kit narrate` (or `draft`)")
        align = meta["alignment"]
        assert "".join(align["characters"]) == meta["text"], f"alignment text mismatch in {sid}"
        end = max(align["character_end_times_seconds"]) + 0.25
        wav = P.AUDIO / f"{sid}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(P.SEGMENTS / f"{sid}.mp3"), "-t", f"{end:.3f}",
                        "-af", f"afade=t=out:st={max(0.0, end - 0.08):.3f}:d=0.08",
                        "-ar", "48000", "-ac", "2", str(wav)], check=True)
        durations[sid] = round(probe_duration(wav), 3)
        alignment[sid] = {"text": meta["text"], "starts": align["character_start_times_seconds"],
                          "ends": align["character_end_times_seconds"]}
        if meta.get("provisional"):
            drafts.append(sid)
    (P.AUDIO / "durations.json").write_text(json.dumps(durations, indent=2))
    (P.AUDIO / "alignment.json").write_text(json.dumps(alignment))
    total = sum(durations.values())
    words = sum(len(c.split()) for _, c, _ in P.segments())
    print(f"{len(durations)} segments, {total:.1f}s of speech, {words} words ({60 * words / total:.0f} wpm)")
    if drafts:
        print(f"{len(drafts)} segments are draft audio: {', '.join(drafts)}")
