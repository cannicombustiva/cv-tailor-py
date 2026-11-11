"""parse_jd against a real (wrapped) OpenAI client whose HTTP transport is mocked: no network."""

import json
from collections.abc import Callable
from typing import Any

import pytest

from cv_tailor_py import llm
from cv_tailor_py.agent import parse_jd
from cv_tailor_py.models import ParsedJD
from cv_tailor_py.prompts import PARSE_SYSTEM

JD_TEXT = "Frontend Engineer. Build product features with React and TypeScript."
PARSED = {
    "role": "Frontend Engineer",
    "seniority": "",
    "requiredSkills": ["React", "TypeScript"],
    "niceToHave": [],
}


def test_parse_jd_returns_parsed_jd(fake_openai: Callable[[dict[str, Any]], list[Any]]) -> None:
    requests = fake_openai({"role": "assistant", "content": json.dumps(PARSED)})

    jd = parse_jd(JD_TEXT)

    assert jd == ParsedJD(
        role="Frontend Engineer",
        seniority="",
        required_skills=["React", "TypeScript"],
        nice_to_have=[],
    )
    (body,) = requests
    assert body["model"] == llm.MODEL
    assert body["messages"] == [
        {"role": "system", "content": PARSE_SYSTEM},
        {"role": "user", "content": JD_TEXT},
    ]
    fmt = body["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["strict"] is True
    schema = fmt["json_schema"]["schema"]
    assert set(schema["required"]) == {"role", "seniority", "requiredSkills", "niceToHave"}
    assert schema["additionalProperties"] is False


def test_parse_jd_raises_on_refusal(fake_openai: Callable[[dict[str, Any]], list[Any]]) -> None:
    fake_openai({"role": "assistant", "content": None, "refusal": "I can't help with that."})

    with pytest.raises(llm.LLMOutputError, match="can't help"):
        parse_jd(JD_TEXT)


def test_parse_jd_logs_function_and_llm_spans(
    fake_openai: Callable[[dict[str, Any]], list[Any]], spans: Any
) -> None:
    fake_openai({"role": "assistant", "content": json.dumps(PARSED)})

    parse_jd(JD_TEXT)

    logged = spans.pop()
    by_name = {s["span_attributes"]["name"]: s for s in logged}
    step = by_name["parse_jd"]
    assert step["span_attributes"]["type"] == "function"
    assert step["output"]["requiredSkills"] == ["React", "TypeScript"]
    llm_spans = [s for s in logged if s["span_attributes"]["type"] == "llm"]
    assert len(llm_spans) == 1
    assert step["span_id"] in llm_spans[0]["span_parents"]


def test_model_defaults_to_gpt_5_mini(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    monkeypatch.delenv("CV_MODEL", raising=False)
    assert importlib.reload(llm).MODEL == "gpt-5-mini"
    monkeypatch.setenv("CV_MODEL", "gpt-x")
    assert importlib.reload(llm).MODEL == "gpt-x"
    monkeypatch.delenv("CV_MODEL")
    importlib.reload(llm)
