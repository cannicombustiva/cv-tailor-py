"""OpenAI client and structured-output helper (TS: llm.ts)."""

import os
from functools import cache

from braintrust import wrap_openai
from openai import OpenAI
from pydantic import BaseModel

MODEL = os.environ.get("CV_MODEL", "gpt-5-mini")


class LLMOutputError(RuntimeError):
    """The model returned no parsed output (refusal or empty message)."""


@cache
def get_client() -> OpenAI:
    """Lazily build the client so importing this module needs no OPENAI_API_KEY.

    wrap_openai makes every call show up as an LLM span inside the active trace.
    """
    client: OpenAI = wrap_openai(OpenAI())
    return client


def structured_call[T: BaseModel](system: str, user: str, schema: type[T]) -> T:
    """Chat completion constrained to `schema` via OpenAI structured outputs (strict JSON schema).

    TS uses `response_format: json_object` and casts; here the response is validated by Pydantic.
    """
    res = get_client().chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=schema,
    )
    message = res.choices[0].message
    if message.parsed is None:
        raise LLMOutputError(message.refusal or "model returned no parsed output")
    return message.parsed
