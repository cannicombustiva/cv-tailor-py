import json
from collections.abc import Callable, Iterator
from typing import Any

import httpx2 as httpx
import pytest
from braintrust import logger, wrap_openai
from braintrust.test_helpers import init_test_logger
from openai import OpenAI

from cv_tailor_py import llm


@pytest.fixture
def spans() -> Iterator[Any]:
    """Capture Braintrust spans in memory (no network). Call `.pop()` to read them."""
    logger._state.reset_parent_state()
    with logger._internal_with_memory_background_logger() as bgl:
        init_test_logger("cv-tailor-py-tests")
        yield bgl
    logger._state.reset_parent_state()


def _completion(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": llm.MODEL,
        "choices": [{"index": 0, "finish_reason": "stop", "message": message}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


@pytest.fixture
def fake_openai(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[dict[str, Any]], list[Any]]]:
    """Install a wrapped OpenAI client whose HTTP transport is mocked (no network).

    Returns a setter for the reply message; the list it returns collects the JSON bodies
    of the requests sent.
    """
    requests: list[Any] = []
    reply: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=_completion(reply))

    client = wrap_openai(
        OpenAI(api_key="test", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    )
    monkeypatch.setattr(llm, "get_client", lambda: client)

    def set_reply(message: dict[str, Any]) -> list[Any]:
        reply.clear()
        reply.update(message)
        return requests

    yield set_reply
