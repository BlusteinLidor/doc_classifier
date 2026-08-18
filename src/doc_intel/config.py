"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_env(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    model: str = "gpt-4o-mini"
    max_chars: int = 20_000
    classify_excerpt_chars: int = 4_000
    max_retries: int = 2
    base_retry_delay_seconds: float = 1.0
    request_timeout_seconds: int = 60
    enable_ocr_fallback: bool = False
    poll_interval_minutes: int = 60
    auto_output_dir: str = "data/auto_runs"
    auto_state_file: str = "data/ingestion_state.json"


def load_config() -> AppConfig:
    return AppConfig(
        model=os.getenv("DOC_INTEL_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini",
        max_chars=_int_env("DOC_INTEL_MAX_CHARS", 20_000),
        classify_excerpt_chars=_int_env("DOC_INTEL_CLASSIFY_EXCERPT_CHARS", 4_000),
        max_retries=_int_env("DOC_INTEL_MAX_RETRIES", 2),
        base_retry_delay_seconds=float(
            os.getenv("DOC_INTEL_RETRY_BASE_DELAY_SECONDS", "1.0")
        ),
        request_timeout_seconds=_int_env("DOC_INTEL_REQUEST_TIMEOUT_SECONDS", 60),
        enable_ocr_fallback=_bool_env("DOC_INTEL_ENABLE_OCR", False),
        poll_interval_minutes=_int_env("DOC_INTEL_POLL_INTERVAL_MINUTES", 60),
        auto_output_dir=(
            os.getenv("DOC_INTEL_AUTO_OUTPUT_DIR", "data/auto_runs").strip()
            or "data/auto_runs"
        ),
        auto_state_file=(
            os.getenv("DOC_INTEL_AUTO_STATE_FILE", "data/ingestion_state.json").strip()
            or "data/ingestion_state.json"
        ),
    )
