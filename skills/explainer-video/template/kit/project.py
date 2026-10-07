"""Project layout, configuration and narration loading.

Every command runs from the project root (the folder holding video.json).
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
CONFIG_FILE = ROOT / "video.json"
BUILD = ROOT / "build"
SEGMENTS = BUILD / "segments"
AUDIO = BUILD / "audio"
TIMINGS = BUILD / "timings"
OUT = ROOT / "out"

DEFAULTS = {
    "name": "explainer",
    "title": "Explainer",
    "resolution": [1920, 1080],
    "fps": 30,
    "font": None,
    "mono_font": None,
    "pause": 0.22,
    "cue_lead": 0.12,
    "loudness": -16,
    "captions": {"burn": True, "line": 50, "size": 13},
    "whisper_prompt": "",
    "voice": {},
}


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def config() -> dict:
    if not CONFIG_FILE.exists():
        raise SystemExit(f"no video.json in {ROOT}; run commands from the project root")
    cfg = _merge(DEFAULTS, json.loads(CONFIG_FILE.read_text()))
    if not cfg["font"]:
        cfg["font"] = "Avenir Next" if sys.platform == "darwin" else "DejaVu Sans"
    if not cfg["mono_font"]:
        cfg["mono_font"] = "Menlo" if sys.platform == "darwin" else "DejaVu Sans Mono"
    return cfg


def _load_module(name: str):
    path = ROOT / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"project_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scenes() -> dict:
    """{scene_name: [(segment_id, caption, spoken), ...]} in playback order.

    narration.py may give a segment as (id, text) when caption and spoken text are identical.
    """
    raw = _load_module("narration").SCENES
    out = {}
    for scene, segs in raw.items():
        out[scene] = [(s[0], s[1], s[2] if len(s) > 2 else s[1]) for s in segs]
    return out


def segments() -> list:
    return [seg for segs in scenes().values() for seg in segs]


def pronunciations() -> list:
    path = ROOT / "pronunciations.json"
    return json.loads(path.read_text()) if path.exists() else []


def aliased(text: str) -> str:
    """Apply pronunciation aliases to spoken text before it is sent to the voice."""
    for rule in pronunciations():
        text = re.sub(rf"\b{re.escape(rule['string_to_replace'])}\b", rule["alias"], text)
    return text


def media_dir(low: bool) -> Path:
    return BUILD / ("media_low" if low else "media")


def clip_path(scene: str, low: bool) -> Path:
    found = sorted((media_dir(low) / scene / "videos").glob(f"*/*/{scene}.mp4"))
    if not found:
        raise SystemExit(f"missing render for {scene}; run `python -m kit render{' --low' if low else ''}`")
    return found[0]
