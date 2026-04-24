"""Application-specific exceptions for PDF and AI pipelines."""


class PDFError(Exception):
    """Raised when a PDF cannot be opened, is encrypted, or yields no usable text."""


class ExtractionError(Exception):
    """Raised when text is empty or extraction prerequisites fail before AI."""


class OpenAIClientError(Exception):
    """Raised when the OpenAI API fails after retries or returns an unusable response."""
