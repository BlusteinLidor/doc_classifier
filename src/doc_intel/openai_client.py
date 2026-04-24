"""OpenAI client wrapper with structured parse and retries."""

from __future__ import annotations

import logging
import time
from typing import TypeVar

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel

from doc_intel.errors import OpenAIClientError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
MAX_RETRIES = 2
BASE_DELAY_SECONDS = 1.0

T = TypeVar("T", bound=BaseModel)


def create_client(api_key: str | None = None) -> OpenAI:
    return OpenAI(api_key=api_key) if api_key else OpenAI()


def parse_structured(
    client: OpenAI,
    *,
    model: str,
    system_prompt: str,
    user_message: str,
    response_model: type[T],
) -> T:
    """
    Call beta.chat.completions.parse with retries on transient failures.

    Raises OpenAIClientError on failure after retries or on bad/empty responses.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    retryable = (RateLimitError, APITimeoutError, APIConnectionError)
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            completion = client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=response_model,
            )
            choice = completion.choices[0]
            msg = choice.message
            if getattr(msg, "refusal", None):
                raise OpenAIClientError("The model refused to process this document.")
            parsed = msg.parsed
            if parsed is None:
                raise OpenAIClientError("The model returned no structured data.")
            return parsed
        except retryable as exc:
            last_error = exc
            logger.warning("OpenAI transient error (attempt %s): %s", attempt + 1, exc)
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY_SECONDS * (2**attempt)
                time.sleep(delay)
                continue
            break
        except APIError as exc:
            logger.exception("OpenAI API error")
            raise OpenAIClientError(
                "The AI service returned an error. Try again later."
            ) from exc
        except OpenAIClientError:
            raise
        except Exception as exc:
            logger.exception("Unexpected OpenAI error")
            raise OpenAIClientError(
                "Could not complete AI extraction. Please try again."
            ) from exc

    raise OpenAIClientError(
        "The AI service is busy or timed out. Please try again in a moment."
    ) from last_error
