"""Scheduler-like polling helpers for in-app auto-ingestion."""

from __future__ import annotations

import time

from doc_intel.config import load_config
from doc_intel.ingestion.gdrive_source import list_new_drive_pdfs
from doc_intel.ingestion.local_source import list_new_local_pdfs
from doc_intel.ingestion.state_store import load_state, save_state
from doc_intel.pipeline import process_pdf_bytes
from doc_intel.storage import save_auto_result


def should_poll(last_poll_unix: float | None) -> bool:
    cfg = load_config()
    if last_poll_unix is None:
        return True
    return (time.time() - last_poll_unix) >= (cfg.poll_interval_minutes * 60)


def run_poll_cycle(
    *,
    source_type: str,
    local_folder: str = "",
    gdrive_folder_id: str = "",
    gdrive_token_json_path: str = "",
    gdrive_client_secret_path: str = "",
) -> list:
    cfg = load_config()
    state = load_state(cfg.auto_state_file)
    seen: dict[str, str] = state.get("seen", {})

    new_docs: list[tuple[str, bytes, str, str]] = []
    if source_type == "local folder":
        for name, data, digest in list_new_local_pdfs(local_folder, seen):
            key = f"local:{name}"
            new_docs.append((key, data, digest, name))
    elif source_type == "google drive":
        for name, data, digest in list_new_drive_pdfs(
            folder_id=gdrive_folder_id,
            token_json_path=gdrive_token_json_path,
            client_secret_path=gdrive_client_secret_path,
            seen=seen,
        ):
            key = f"gdrive:{name}"
            new_docs.append((key, data, digest, name))

    results = []
    for key, data, digest, name in new_docs:
        result = process_pdf_bytes(name, data, model=cfg.model)
        save_auto_result(cfg.auto_output_dir, result)
        seen[key] = digest
        results.append(result)

    state["seen"] = seen
    save_state(cfg.auto_state_file, state)
    return results
