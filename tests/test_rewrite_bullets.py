"""rewrite_bullets against a real (wrapped) OpenAI client whose HTTP transport is mocked."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from cv_tailor_py import llm
from cv_tailor_py.agent import match_profile, rewrite_bullets
from cv_tailor_py.cli import load_profile
from cv_tailor_py.models import ParsedJD, Rewritten
from cv_tailor_py.prompts import REWRITE_SYSTEM

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN: dict[str, Any] = json.loads((FIXTURES / "golden.json").read_text())["match"]
CASES = {c["id"]: c for c in json.loads((FIXTURES / "match_cases.json").read_text())}

FakeOpenAI = Callable[[dict[str, Any]], list[Any]]
REPLY = {
    "summary": "Engineer with one fact.",
    "bullets": [{"id": "t2", "text": "Shipped two matches"}, {"id": "t5", "text": "Delivered"}],
}


def _setup(case_id: str = "tiebreak") -> tuple[Any, Any, ParsedJD]:
    case = CASES[case_id]
    profile = load_profile(ROOT / case["profile"])
    jd = ParsedJD.model_validate(case["jd"])
    return profile, match_profile(profile, jd), jd


def _reply(fake_openai: FakeOpenAI, content: dict[str, Any] = REPLY) -> list[Any]:
    return fake_openai({"role": "assistant", "content": json.dumps(content)})


def test_rewrite_bullets_returns_rewritten(fake_openai: FakeOpenAI) -> None:
    _reply(fake_openai)
    profile, roles, jd = _setup()

    out = rewrite_bullets(profile, roles, jd)

    assert out == Rewritten(
        summary="Engineer with one fact.",
        bullets={"t2": "Shipped two matches", "t5": "Delivered"},
    )


@pytest.mark.parametrize("case_id", list(CASES))
def test_request_matches_ts_input(fake_openai: FakeOpenAI, case_id: str) -> None:
    requests = _reply(fake_openai)
    profile, roles, jd = _setup(case_id)

    rewrite_bullets(profile, roles, jd)

    (body,) = requests
    assert body["model"] == llm.MODEL
    assert body["messages"] == [
        {"role": "system", "content": REWRITE_SYSTEM},
        {"role": "user", "content": GOLDEN[case_id]["rewriteInput"]},
    ]
    fmt = body["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["strict"] is True


def test_llm_sees_only_selected_facts(fake_openai: FakeOpenAI) -> None:
    requests = _reply(fake_openai)
    profile, roles, jd = _setup()

    rewrite_bullets(profile, roles, jd)

    sent = json.loads(requests[0]["messages"][1]["content"])
    assert set(sent) == {"target", "facts"}
    assert set(sent["facts"]) == {"summaryFacts", "achievements"}
    assert [a["id"] for a in sent["facts"]["achievements"]] == [
        "t2",
        "t5",
        "t1",
        "t3",
        "t6",
        "z2",
        "z1",
    ]
    for a in sent["facts"]["achievements"]:
        assert set(a) == {"id", "text"}  # no per-achievement skills
    user = requests[0]["messages"][1]["content"]
    for leaked in ("No match", "fourth (cut)", profile.name, profile.email, profile.location):
        assert leaked not in user


def test_response_schema_is_strict_list_of_bullets(fake_openai: FakeOpenAI) -> None:
    requests = _reply(fake_openai)
    rewrite_bullets(*_setup())

    schema = requests[0]["response_format"]["json_schema"]["schema"]
    assert set(schema["required"]) == {"summary", "bullets"}
    assert schema["additionalProperties"] is False
    assert schema["properties"]["bullets"]["type"] == "array"


def test_rewrite_bullets_raises_on_refusal(fake_openai: FakeOpenAI) -> None:
    fake_openai({"role": "assistant", "content": None, "refusal": "I can't help with that."})

    with pytest.raises(llm.LLMOutputError, match="can't help"):
        rewrite_bullets(*_setup())


def test_rewrite_bullets_logs_function_and_llm_spans(fake_openai: FakeOpenAI, spans: Any) -> None:
    _reply(fake_openai)
    profile, roles, jd = _setup()

    rewrite_bullets(profile, roles, jd)

    logged = spans.pop()
    (step,) = [s for s in logged if s["span_attributes"]["name"] == "rewrite_bullets"]
    assert step["span_attributes"]["type"] == "function"
    assert step["output"]["bullets"] == {"t2": "Shipped two matches", "t5": "Delivered"}
    llm_spans = [s for s in logged if s["span_attributes"]["type"] == "llm"]
    assert len(llm_spans) == 1
    assert step["span_id"] in llm_spans[0]["span_parents"]
