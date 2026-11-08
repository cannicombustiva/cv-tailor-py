"""Command-line entry point for cv-tailor-py."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from cv_tailor_py.models import Profile


def load_profile(path: Path) -> Profile:
    """Read and validate a profile JSON file."""
    return Profile.model_validate_json(path.read_bytes())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cv-tailor-py",
        description="Tailor a CV profile to a job description.",
    )
    parser.add_argument("profile", type=Path, help="path to the profile JSON file")
    parser.add_argument("job", type=Path, help="path to the job JSON file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    profile_path: Path = args.profile

    try:
        profile = load_profile(profile_path)
    except OSError as exc:
        print(f"error: cannot read profile {profile_path}: {exc}", file=sys.stderr)
        return 1
    except ValidationError as exc:
        print(f"error: invalid profile {profile_path}:\n{exc}", file=sys.stderr)
        return 1

    achievements = sum(len(role.achievements) for role in profile.roles)
    print(
        f"Loaded profile '{profile.name}': "
        f"{len(profile.roles)} roles, {achievements} achievements, "
        f"{len(profile.skills)} skills."
    )
    return 0
