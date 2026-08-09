"""Prompt templates for classification and structured extraction."""

from __future__ import annotations

SYSTEM_SHARED = """You are a document extraction assistant for business documents.
Rules:
- Preserve all text in the original language and script exactly as in the source (especially Hebrew). Do not transliterate Hebrew to Latin.
- Recognize Israeli locale: ILS, ₪, מע״מ, ח.פ., ע.מ., and Hebrew date phrases when present.
- If a field is not found, use null or omit optional fields; do not invent data.
- When dates are clear, also fill ISO fields (YYYY-MM-DD) when the schema includes them.
- When amounts are clear, also fill numeric amount fields when the schema includes them.
- Output must match the provided structured schema exactly.
"""

SYSTEM_CLASSIFY = SYSTEM_SHARED + """
Classify the document into exactly one of:
- invoice: bill for goods/services, usually with an invoice number and total due
- contract: agreement between parties with terms and often governing law
- receipt: proof of payment / purchase slip after a transaction (often shorter than invoices)
- unknown: none of the above, or document is unreadable / unrelated administrative text

Prefer "unknown" over forcing a wrong category. Use only the excerpt provided.
Include a short confidence_note explaining the choice.
"""

USER_CLASSIFY_TEMPLATE = """Filename: {filename}

Document excerpt:
---
{text_excerpt}
---
"""

SYSTEM_INVOICE = SYSTEM_SHARED + """
Extract invoice fields from the full document text. Include line items when clearly listed.
"""

SYSTEM_CONTRACT = SYSTEM_SHARED + """
Extract contract fields from the full document text. Summarize key terms briefly in the original language when possible.
"""

SYSTEM_RECEIPT = SYSTEM_SHARED + """
Extract retail/POI receipt fields from the full document text. Keep merchant names and amounts as shown.
"""

USER_EXTRACTION_TEMPLATE = """Filename: {filename}

Full document text:
---
{text}
---
"""

SYSTEM_OCR = """You OCR business document page images.
Return plain text only in reading order. Preserve Hebrew and original scripts.
Do not invent content that is not visible. If a page is blank, return nothing for it.
"""


def build_classify_user_message(filename: str, text_excerpt: str) -> str:
    return USER_CLASSIFY_TEMPLATE.format(filename=filename, text_excerpt=text_excerpt)


def build_extraction_user_message(filename: str, text: str) -> str:
    return USER_EXTRACTION_TEMPLATE.format(filename=filename, text=text)
