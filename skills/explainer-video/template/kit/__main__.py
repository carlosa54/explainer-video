"""python -m kit <command> [options], run from the project root.

  voices [--mine]              list stock voices (or your own / cloned ones)
  audition VOICE[:MODEL] ...   one hard sentence per voice, into build/audition/
  draft                        free placeholder narration (macOS say / espeak-ng) for layout
  narrate [--dry-run]          ElevenLabs narration with timestamps; cached by content
  audio                        trim segments, write durations and alignment for the scenes
  render [--low] [Scene ...]   render scenes with Manim in parallel
  timing                       scene lengths and silent gaps
  assemble [--low] [--draft]   final MP4, SRT, contact sheet and timestamped script in out/
  build [--low] [--draft]      audio + render + assemble
  verify [--low] [--speech]    decode and loudness; --speech adds Whisper checks
"""

import sys

from .assemble import cmd_assemble
from .audio import cmd_audio
from .render import cmd_render, cmd_timing
from .tts import cmd_audition, cmd_draft, cmd_narrate, cmd_voices
from .verify import cmd_verify


def cmd_build(args):
    cmd_audio(args)
    cmd_render([a for a in args if a == "--low"])
    cmd_assemble(args)


COMMANDS = {"voices": cmd_voices, "audition": cmd_audition, "draft": cmd_draft, "narrate": cmd_narrate,
            "audio": cmd_audio, "render": cmd_render, "timing": cmd_timing, "assemble": cmd_assemble,
            "build": cmd_build, "verify": cmd_verify}

if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
    sys.exit(__doc__)
COMMANDS[sys.argv[1]](sys.argv[2:])
