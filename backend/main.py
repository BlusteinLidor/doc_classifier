"""FastAPI app: health, samples, process (SSE), static SPA."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from doc_intel.export import (  # noqa: E402
    branded_export_basename,
    results_to_csv_bytes,
)
from doc_intel.models import ProcessingResult  # noqa: E402
from doc_intel.pipeline import process_pdf_bytes  # noqa: E402

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_SAMPLES_DIR = _ROOT / "samples"
_FRONTEND_DIST = _ROOT / "frontend" / "dist"
_MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB
_MAX_FILES_PER_RUN = 3
_FEATURED_SAMPLE = "sample_invoice_he.pdf"

# filename, teaser_en, teaser_he, label_en, label_he, featured, kind
_SAMPLE_DOCS: list[tuple[str, str, str, str, str, bool, str]] = [
    (
        "sample_invoice_en.pdf",
        "USD totals · vendor & line items",
        "סכומים בדולר · ספק ופריטים",
        "English invoice",
        "חשבונית אנגלית",
        False,
        "invoice",
    ),
    (
        "sample_invoice_he.pdf",
        "₪ amounts · Hebrew vendor",
        "סכומים ₪ · ספק בעברית",
        "Hebrew invoice",
        "חשבונית בעברית",
        True,
        "invoice",
    ),
    (
        "sample_contract_en.pdf",
        "Two parties · governing law",
        "שני צדדים · דין חל",
        "English contract",
        "חוזה באנגלית",
        False,
        "contract",
    ),
    (
        "sample_contract_he.pdf",
        "Hebrew parties · key terms",
        "צדדים בעברית · תנאים עיקריים",
        "Hebrew contract",
        "חוזה בעברית",
        False,
        "contract",
    ),
    (
        "sample_receipt_en.pdf",
        "Merchant slip · payment method",
        "קבלה · אמצעי תשלום",
        "English receipt",
        "קבלה באנגלית",
        False,
        "receipt",
    ),
    (
        "sample_receipt_he.pdf",
        "Hebrew merchant · ₪ total",
        "בית עסק בעברית · סה״כ ₪",
        "Hebrew receipt",
        "קבלה בעברית",
        False,
        "receipt",
    ),
    (
        "sample_quote_en.pdf",
        "Proposal · validity period",
        "הצעת מחיר · תוקף",
        "English quote",
        "הצעת מחיר באנגלית",
        False,
        "quote",
    ),
    (
        "sample_purchase_order_en.pdf",
        "Buyer PO · line items",
        "הזמנת רכש · פריטים",
        "English purchase order",
        "הזמנת רכש באנגלית",
        False,
        "purchase_order",
    ),
    (
        "sample_bank_statement_en.pdf",
        "Period · balances & transactions",
        "תקופה · יתרות ותנועות",
        "English bank statement",
        "דף חשבון באנגלית",
        False,
        "bank_statement",
    ),
]


class SampleMeta(BaseModel):
    filename: str
    teaser_en: str
    teaser_he: str
    label_en: str
    label_he: str
    featured: bool
    kind: str


class ProcessSampleBody(BaseModel):
    filename: str = Field(..., description="Sample PDF filename under samples/.")


class ExportBody(BaseModel):
    results: list[dict[str, Any]]


app = FastAPI(
    title="AI Document Intelligence",
    description="Portfolio demo API",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sample_meta_list() -> list[SampleMeta]:
    return [
        SampleMeta(
            filename=fn,
            teaser_en=te_en,
            teaser_he=te_he,
            label_en=lb_en,
            label_he=lb_he,
            featured=feat,
            kind=kind,
        )
        for fn, te_en, te_he, lb_en, lb_he, feat, kind in _SAMPLE_DOCS
    ]


def _load_sample(filename: str) -> bytes:
    # Prevent path traversal
    safe = Path(filename).name
    if safe != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid sample filename.")
    path = _SAMPLES_DIR / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Sample not found: {safe}")
    return path.read_bytes()


def _validate_pdf_payload(filename: str, data: bytes) -> None:
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    if len(data) > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds demo size limit ({_MAX_FILE_BYTES // (1024 * 1024)} MB).",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")


def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


async def _stream_process_files(
    files: list[tuple[str, bytes]],
) -> AsyncIterator[str]:
    """Yield SSE events: stage, result, done (or error)."""
    if not files:
        yield _sse({"type": "error", "message": "No files to process."})
        return
    if len(files) > _MAX_FILES_PER_RUN:
        yield _sse(
            {
                "type": "error",
                "message": f"Demo limit: at most {_MAX_FILES_PER_RUN} files per run.",
            }
        )
        return

    loop = asyncio.get_running_loop()
    all_results: list[dict[str, Any]] = []

    for idx, (name, data) in enumerate(files):
        yield _sse(
            {
                "type": "file_start",
                "filename": name,
                "index": idx,
                "total": len(files),
            }
        )

        try:
            _validate_pdf_payload(name, data)
        except HTTPException as exc:
            fail = ProcessingResult(
                filename=name,
                success=False,
                error_message=str(exc.detail),
            )
            payload = fail.model_dump(mode="json")
            all_results.append(payload)
            yield _sse({"type": "result", "result": payload})
            continue

        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

        def on_stage(msg: str, _q: asyncio.Queue = queue) -> None:
            fut = asyncio.run_coroutine_threadsafe(
                _q.put({"type": "stage", "filename": name, "message": msg}),
                loop,
            )
            try:
                fut.result(timeout=5)
            except Exception:
                logger.exception("Failed to enqueue stage message")

        def run_one(
            _name: str = name,
            _data: bytes = data,
            _on_stage=on_stage,
            _q: asyncio.Queue = queue,
        ) -> None:
            try:
                result = process_pdf_bytes(_name, _data, on_stage=_on_stage)
                payload = result.model_dump(mode="json")
                asyncio.run_coroutine_threadsafe(
                    _q.put({"type": "result", "result": payload}),
                    loop,
                ).result(timeout=30)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Process failed for %s", _name)
                fail = ProcessingResult(
                    filename=_name,
                    success=False,
                    error_message=str(exc),
                )
                asyncio.run_coroutine_threadsafe(
                    _q.put({"type": "result", "result": fail.model_dump(mode="json")}),
                    loop,
                ).result(timeout=30)
            finally:
                asyncio.run_coroutine_threadsafe(_q.put(None), loop).result(timeout=5)

        loop.run_in_executor(None, run_one)

        while True:
            item = await queue.get()
            if item is None:
                break
            if item.get("type") == "result":
                all_results.append(item["result"])
            yield _sse(item)

    yield _sse({"type": "done", "results": all_results})


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "featured_sample": _FEATURED_SAMPLE,
        "max_files": _MAX_FILES_PER_RUN,
        "max_mb": _MAX_FILE_BYTES // (1024 * 1024),
    }


@app.get("/api/samples", response_model=list[SampleMeta])
def list_samples() -> list[SampleMeta]:
    return _sample_meta_list()


@app.get("/api/samples/{filename}")
def get_sample(filename: str) -> Response:
    data = _load_sample(filename)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{Path(filename).name}"',
            "Cache-Control": "public, max-age=3600",
        },
    )


@app.post("/api/process/sample")
async def process_sample_stream(body: ProcessSampleBody) -> StreamingResponse:
    """Process a built-in sample by filename (SSE)."""
    try:
        data = _load_sample(body.filename)
    except HTTPException:
        raise
    return StreamingResponse(
        _stream_process_files([(Path(body.filename).name, data)]),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/process")
async def process_upload_stream(
    files: list[UploadFile] = File(...),
) -> StreamingResponse:
    """Process uploaded PDFs (SSE). Max 3 files, 5 MB each."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    if len(files) > _MAX_FILES_PER_RUN:
        raise HTTPException(
            status_code=400,
            detail=f"Demo limit: at most {_MAX_FILES_PER_RUN} files per run.",
        )

    prepared: list[tuple[str, bytes]] = []
    for f in files[:_MAX_FILES_PER_RUN]:
        name = f.filename or "upload.pdf"
        data = await f.read()
        prepared.append((Path(name).name, data))

    return StreamingResponse(
        _stream_process_files(prepared),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _coerce_results(raw: list[dict[str, Any]]) -> list[ProcessingResult]:
    """Rebuild ProcessingResult using doc_type to pick the structured schema."""
    from doc_intel.registry import get_type_spec

    out: list[ProcessingResult] = []
    for item in raw:
        payload = dict(item)
        st = payload.pop("structured", None)
        doc_type = payload.get("doc_type")
        base = ProcessingResult.model_validate({**payload, "structured": None})
        if isinstance(st, dict) and doc_type:
            spec = get_type_spec(str(doc_type))
            if spec is not None:
                base.structured = spec.schema.model_validate(st)
        out.append(base)
    return out


@app.post("/api/export/json")
def export_json(body: ExportBody) -> Response:
    data = json.dumps(body.results, ensure_ascii=False, indent=2).encode("utf-8")
    name = f"{branded_export_basename()}.json"
    return Response(
        content=data,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@app.post("/api/export/csv")
def export_csv(body: ExportBody) -> Response:
    results = _coerce_results(body.results)
    data = results_to_csv_bytes(results)
    name = f"{branded_export_basename()}.csv"
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


# Static SPA (production build). Must be registered after API routes.
if _FRONTEND_DIST.is_dir():
    assets = _FRONTEND_DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/")
    def spa_index() -> FileResponse:
        index = _FRONTEND_DIST / "index.html"
        if not index.is_file():
            raise HTTPException(status_code=404, detail="Frontend not built.")
        return FileResponse(index)

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (_FRONTEND_DIST / full_path).resolve()
        try:
            candidate.relative_to(_FRONTEND_DIST.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="Not found") from None
        if candidate.is_file():
            return FileResponse(candidate)
        index = _FRONTEND_DIST / "index.html"
        if not index.is_file():
            raise HTTPException(status_code=404, detail="Frontend not built.")
        return FileResponse(index)


def create_app() -> FastAPI:
    return app
