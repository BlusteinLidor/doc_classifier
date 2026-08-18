"""State persistence for auto-ingestion dedupe/checkpoints."""

from __future__ import annotations

import json
from pathlib import Path


def load_state(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"seen": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"seen": {}}


def save_state(path: str, state: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
