"""Local folder ingestion source."""

from __future__ import annotations

import hashlib
from pathlib import Path


def list_new_local_pdfs(folder: str, seen: dict[str, str]) -> list[tuple[str, bytes, str]]:
    out: list[tuple[str, bytes, str]] = []
    root = Path(folder)
    if not root.exists() or not root.is_dir():
        return out
    for path in sorted(root.glob("*.pdf")):
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        key = str(path.resolve())
        if seen.get(key) == digest:
            continue
        out.append((path.name, data, digest))
    return out
