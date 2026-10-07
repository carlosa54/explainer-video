#!/usr/bin/env python3
"""Create a video project.

  new_project.py DEST               start from the bundled example (kit + sample script and scenes)
  new_project.py DEST --from SRC    start a new cut from an existing project; SRC is left untouched

The kit is always copied fresh from this skill, so a new cut picks up kit fixes.
Synthesized narration is cached outside the project, so a new cut re-uses every
sentence that did not change.
"""

import shutil
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "template"
SKIP = shutil.ignore_patterns("build", "out", "__pycache__", "*.pyc", ".venv", "media")


def main(argv):
    if not argv or argv[0].startswith("-"):
        raise SystemExit(__doc__)
    dest = Path(argv[0]).expanduser().resolve()
    src = Path(argv[argv.index("--from") + 1]).expanduser().resolve() if "--from" in argv else TEMPLATE
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"{dest} exists and is not empty; pick a new folder so earlier cuts stay intact")
    if not (src / "video.json").exists():
        raise SystemExit(f"{src} is not a video project (no video.json)")
    shutil.copytree(src, dest, ignore=SKIP, dirs_exist_ok=True)
    shutil.rmtree(dest / "kit", ignore_errors=True)
    shutil.copytree(TEMPLATE / "kit", dest / "kit", ignore=SKIP)
    (dest / ".gitignore").write_text("build/\nout/\n__pycache__/\n.venv/\n")
    print(f"created {dest} from {src}")
    print("next: cd into it, install requirements.txt, then `python -m kit draft && python -m kit build --low`")


if __name__ == "__main__":
    main(sys.argv[1:])
