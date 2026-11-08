import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from cv_tailor_py.cli import load_profile, main
from cv_tailor_py.models import JobSpec, Profile

DATA = Path(__file__).resolve().parent.parent / "data"
PROFILE_PATH = DATA / "profile.example.json"
JOBS_PATH = DATA / "jobs.example.json"


def _profile_dict() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(PROFILE_PATH.read_text())
    return data


def test_loads_example_profile() -> None:
    profile = load_profile(PROFILE_PATH)

    assert profile.name == "Example Candidate"
    assert len(profile.summary_facts) == 3
    assert "React" in profile.skills
    assert [r.company for r in profile.roles] == ["Company A", "Company B"]
    assert [a.id for a in profile.roles[0].achievements] == ["a1", "a2", "a3", "a4"]
    assert profile.roles[0].achievements[0].skills == ["React", "TypeScript"]
    assert profile.education[0].degree == "BSc Computer Science"


def test_profile_round_trips_to_camel_case_json() -> None:
    profile = load_profile(PROFILE_PATH)
    assert profile.model_dump(by_alias=True) == _profile_dict()


def test_loads_example_jobs() -> None:
    jobs = [JobSpec.model_validate(j) for j in json.loads(JOBS_PATH.read_text())]

    assert [j.id for j in jobs] == ["senior-frontend", "frontend-graphql", "fullstack-node"]
    assert jobs[1].required_skills == ["React", "TypeScript", "GraphQL"]


def test_rejects_profile_missing_required_field() -> None:
    data = _profile_dict()
    del data["name"]

    with pytest.raises(ValidationError, match="name"):
        Profile.model_validate(data)


def test_rejects_profile_with_wrong_type() -> None:
    data = _profile_dict()
    data["roles"][0]["achievements"] = "not a list"

    with pytest.raises(ValidationError, match="achievements"):
        Profile.model_validate(data)


def test_rejects_profile_with_unknown_field() -> None:
    data = _profile_dict()
    data["summary_facts_typo"] = []

    with pytest.raises(ValidationError, match="summary_facts_typo"):
        Profile.model_validate(data)


def test_cli_loads_valid_profile(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(PROFILE_PATH), str(JOBS_PATH)]) == 0
    assert "Example Candidate" in capsys.readouterr().out


def test_cli_rejects_invalid_profile(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"name": "x"}))

    assert main([str(bad), str(JOBS_PATH)]) == 1
    assert "invalid profile" in capsys.readouterr().err


def test_cli_reports_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(tmp_path / "nope.json"), str(JOBS_PATH)]) == 1
    assert "cannot read profile" in capsys.readouterr().err


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "profile" in out and "job" in out
