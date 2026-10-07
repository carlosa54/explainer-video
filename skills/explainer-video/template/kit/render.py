"""Render scenes with Manim in parallel, then report timing."""

import json
import os
import subprocess
import sys

from . import project as P


def cmd_render(args):
    """Render every scene (or the named ones). --low renders a fast 480p15 preview."""
    low = "--low" in args
    names = [a for a in args if not a.startswith("--")]
    cfg = P.config()
    order = list(P.scenes())
    unknown = [n for n in names if n not in order]
    if unknown:
        raise SystemExit(f"unknown scenes {unknown}; narration.py defines {order}")
    w, h = (854, 480) if low else cfg["resolution"]
    fps = 15 if low else cfg["fps"]
    logs = P.BUILD / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONPATH": f"{P.ROOT}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"}
    jobs = {}
    for scene in names or order:
        cmd = [sys.executable, "-m", "manim", "render", "scenes.py", scene, "--resolution", f"{w},{h}",
               "--frame_rate", str(fps), "--media_dir", str(P.media_dir(low) / scene), "--disable_caching",
               "-v", "WARNING"]
        # stdin is closed so a bad scene name fails instead of waiting at Manim's scene picker.
        jobs[scene] = subprocess.Popen(cmd, cwd=P.ROOT, env=env, stdin=subprocess.DEVNULL,
                                       stdout=open(logs / f"{scene}.log", "w"), stderr=subprocess.STDOUT)
    failed = [s for s, p in jobs.items() if p.wait() != 0]
    for scene in jobs:
        print("FAILED" if scene in failed else "ok", scene, "" if scene not in failed else f"(see build/logs/{scene}.log)")
    if failed:
        raise SystemExit(1)
    cmd_timing([])


def cmd_timing(args):
    """Scene lengths, and any gap where the picture keeps moving after the voice has stopped."""
    total = 0.0
    for scene in P.scenes():
        path = P.TIMINGS / f"{scene}.json"
        if not path.exists():
            print(f"{scene:<14} not rendered")
            continue
        data = json.loads(path.read_text())
        segs = data["segments"]
        ends = [s["start"] for s in segs[1:]] + [data["length"]]
        for i, (cur, nxt) in enumerate(zip(segs, ends)):
            slack = nxt - cur["start"] - cur["duration"]
            # The last segment of a scene legitimately holds for the closing beat and fade-out.
            if slack > (1.2 if i + 1 < len(segs) else 3.0):
                print(f"  {scene}.{cur['id']}: {slack:.2f}s of silence after the speech (animations overran it)")
        total += data["length"]
        print(f"{scene:<14} {data['length']:6.2f}s")
    print(f"{'total':<14} {total:6.2f}s ({int(total // 60)}:{total % 60:05.2f})")
