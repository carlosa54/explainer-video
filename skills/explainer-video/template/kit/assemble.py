"""Join rendered scenes, lay down one narration track, and produce captions, a contact sheet and a script.

Outputs in out/:
  <name>.mp4              H.264 + AAC, burned captions, soft English subtitle track
  <name>.srt              captions timed from the voice's character alignment
  <name>-contact.png      one frame every 10 seconds, for reviewing the whole film at a glance
  <name>-script.md        narration by scene with timestamps
"""

import json
import re
import subprocess
import textwrap

from . import project as P
from .audio import probe_duration

SENT = re.compile(r"(?<=[.?!])\s+")


def _sentence_spans(text: str):
    spans, pos = [], 0
    for part in SENT.split(text):
        start = text.index(part, pos)
        spans.append((start, start + len(part)))
        pos = start + len(part)
    return spans


def _cards(align, caption, offset, line):
    """Caption cards for one segment: each caption sentence is timed from the matching spoken sentence."""
    spoken, starts, ends = align["text"], align["starts"], align["ends"]
    cap_sentences = SENT.split(caption)
    spans = _sentence_spans(spoken)
    if len(cap_sentences) != len(spans):
        raise SystemExit(f"caption and spoken text must have the same sentences:\n  {caption!r}\n  {spoken!r}")
    timed = []
    for sentence, (a, b) in zip(cap_sentences, spans):
        pieces = textwrap.wrap(sentence, line)
        cards = ["\n".join(pieces[i:i + 2]) for i in range(0, len(pieces), 2)]
        total, done = sum(len(c) for c in cards), 0
        for card in cards:
            # A long sentence splits into several cards: map each card's share of the caption
            # characters onto the spoken sentence, then read the real timestamps there.
            ca = a + round((b - a) * done / total)
            done += len(card)
            cb = a + round((b - a) * done / total) - 1
            timed.append([offset + starts[ca], offset + ends[max(ca, cb)], card])
    merged = []
    for card in timed:
        prev = merged[-1] if merged else None
        joined = f"{prev[2]} {card[2]}" if prev else ""
        if prev and "\n" not in prev[2] and "\n" not in card[2] and len(joined) <= 2 * line and card[0] - prev[1] < 0.6:
            prev[1] = card[1]
            prev[2] = "\n".join(textwrap.wrap(joined, line))
        else:
            merged.append(card)
    return merged


def _stamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def cmd_assemble(args):
    """Build the final video. --low assembles the 480p preview; --draft allows placeholder audio (watermarked)."""
    low, draft = "--low" in args, "--draft" in args
    cfg = P.config()
    if not (P.AUDIO / "alignment.json").exists():
        raise SystemExit("no prepared audio; run `python -m kit audio` and `render` first (or `build`)")
    drafts = [sid for sid, *_ in P.segments() if json.loads((P.SEGMENTS / f"{sid}.json").read_text()).get("provisional")]
    if drafts and not (draft or low):
        raise SystemExit(f"{len(drafts)} segments are still draft audio ({', '.join(drafts[:5])}...). "
                         "Run `python -m kit narrate`, or pass --draft for a watermarked preview.")
    align = json.loads((P.AUDIO / "alignment.json").read_text())
    captions = {sid: caption for sid, caption, _ in P.segments()}
    line = cfg["captions"]["line"]
    suffix = "-preview" if (low or drafts) else ""
    P.OUT.mkdir(exist_ok=True)
    out = P.OUT / f"{cfg['name']}{suffix}.mp4"
    srt = P.OUT / f"{cfg['name']}{suffix}.srt"
    build = P.BUILD / ("assemble_low" if low else "assemble")
    build.mkdir(parents=True, exist_ok=True)

    clips, cues, rows, placements, t = [], [], [], [], 0.0
    for scene in P.scenes():
        clip = P.clip_path(scene, low)
        clips.append(clip)
        for seg in json.loads((P.TIMINGS / f"{scene}.json").read_text())["segments"]:
            start = t + seg["start"]
            placements.append((seg["id"], start))
            cues += _cards(align[seg["id"]], captions[seg["id"]], start, line)
            rows.append((scene, start, captions[seg["id"]]))
        t += probe_duration(clip)

    # Hold each card until just before the next one, so short gaps don't flicker.
    for cur, nxt in zip(cues, cues[1:]):
        cur[1] = nxt[0] - 0.04 if nxt[0] - cur[1] < 0.5 else cur[1] + 0.3
    cues[-1][1] += 0.3
    srt.write_text("".join(f"{i}\n{_stamp(a)} --> {_stamp(b)}\n{text}\n\n" for i, (a, b, text) in enumerate(cues, 1)))

    concat = build / "concat.txt"
    concat.write_text("".join(f"file '{c}'\n" for c in clips))
    joined = build / "joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-map", "0:v", "-c", "copy", str(joined)], check=True)

    # One narration track: each segment placed at its recorded start, rather than trusting Manim's mixed audio.
    narration = build / "narration.wav"
    inputs, labels, graph = [], [], []
    for i, (sid, start) in enumerate(placements):
        inputs += ["-i", str(P.AUDIO / f"{sid}.wav")]
        ms = int(round(start * 1000))
        graph.append(f"[{i}:a]adelay={ms}|{ms}[d{i}]")
        labels.append(f"[d{i}]")
    graph.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:dropout_transition=0,apad,atrim=0:{t:.3f}[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(graph),
                    "-map", "[a]", "-ar", "48000", "-ac", "2", str(narration)], check=True)

    vf = []
    if cfg["captions"]["burn"]:
        style = (f"FontName={cfg['font']},FontSize={cfg['captions']['size']},PrimaryColour=&H00F2ECE8,BackColour=&H66000000,"
                 "OutlineColour=&H99000000,BorderStyle=4,Outline=0,Shadow=0,MarginV=14,Alignment=2")
        vf.append(f"subtitles='{str(srt).replace(':', chr(92) + ':')}':force_style='{style}'")
    if drafts:
        vf.append("drawtext=text='DRAFT AUDIO':x=w-tw-24:y=24:fontsize=h/30:fontcolor=white@0.7:box=1:boxcolor=red@0.5:boxborderw=8")
    w, h = (854, 480) if low else cfg["resolution"]
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), "-i", str(narration), "-i", str(srt),
        "-filter_complex", f"[0:v]{','.join(vf) or 'null'}[v];[1:a]loudnorm=I={cfg['loudness']}:TP=-1.5:LRA=11,aresample=48000[a]",
        "-map", "[v]", "-map", "[a]", "-map", "2:s",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
        "-metadata", f"title={cfg['title']}", "-movflags", "+faststart", str(out)], check=True)

    sheet = P.OUT / f"{cfg['name']}{suffix}-contact.png"
    rows_needed = max(1, -(-int(probe_duration(out) // 10 + 1) // 5))
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-vf",
        "fps=1/10,scale=480:-2,drawtext=text='%{pts\\:gmtime\\:0\\:%M\\\\\\:%S}':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,"
        f"tile=5x{rows_needed}:padding=6:color=0x05070b",
        "-frames:v", "1", str(sheet)], check=True)

    voice = cfg["voice"]
    lines = [f"# {cfg['title']}: narration script", "",
             f"Voice: {voice.get('voice_name', voice.get('voice_id'))} ({voice.get('voice_id')}) on `{voice.get('model_id')}`."
             + (" Draft audio in some segments." if drafts else ""),
             "Timestamps come from the final render; captions are shown, spoken forms live in narration.py.", ""]
    current = None
    for scene, start, text in rows:
        if scene != current:
            lines += ["", f"## {scene}", ""]
            current = scene
        lines.append(f"- **{int(start // 60)}:{start % 60:04.1f}** {text}")
    (P.OUT / f"{cfg['name']}{suffix}-script.md").write_text("\n".join(lines) + "\n")
    print(f"{out} {probe_duration(out):.1f}s ({w}x{h}), {len(cues)} captions")
