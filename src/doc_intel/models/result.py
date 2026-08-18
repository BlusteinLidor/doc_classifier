"""Result/transport models for UI, exports, and automation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from doc_intel.models.common import DocumentMetadata
from doc_intel.models.contract import ContractExtraction
from doc_intel.models.invoice import InvoiceExtraction


class DocumentKindResult(BaseModel):
    kind: Literal["invoice", "contract"] = Field(
        description="Whether the document is primarily an invoice or a contract."
    )
    confidence_note: str | None = Field(
        default=None,
        description="Short optional note on why this classification was chosen.",
    )


class ProcessingResult(BaseModel):
    filename: str
    success: bool
    doc_type: Literal["invoice", "contract"] | None = None
    structured: InvoiceExtraction | ContractExtraction | None = None
    raw_text_preview: str = ""
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    request_id: str | None = None
    document_metadata: DocumentMetadata | None = None
