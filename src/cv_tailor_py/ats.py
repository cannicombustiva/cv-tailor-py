"""ATS heuristics, ported 1:1 from cv-tailor/src/ats.ts."""

import re

from cv_tailor_py.models import AtsReport, ParsedJD

STANDARD_HEADINGS = ["summary", "experience", "skills", "education"]

_NON_KEYWORD = re.compile(r"[^a-z0-9+#.\s]")
# TS: /\.(?=\s|$)/ — JS `$` without the m flag is end of input, which is `\Z` in Python.
_TRAILING_DOT = re.compile(r"\.(?=\s|\Z)")
_WHITESPACE = re.compile(r"\s+")


def normalize(s: str) -> str:
    s = _NON_KEYWORD.sub(" ", s.lower())
    s = _TRAILING_DOT.sub(" ", s)
    return _WHITESPACE.sub(" ", s).strip()


def keyword_coverage(cv: str, required_skills: list[str]) -> tuple[float, list[str]]:
    """Share of required skills found as whole words in the CV, plus the missing ones."""
    text = f" {normalize(cv)} "
    missing = [s for s in required_skills if f" {normalize(s)} " not in text]
    score = 1.0 if not required_skills else 1 - len(missing) / len(required_skills)
    return score, missing


def run_ats_checks(cv: str, jd: ParsedJD) -> AtsReport:
    score, missing = keyword_coverage(cv, jd.required_skills)
    lines = cv.split("\n")
    headings = [line[3:].strip().lower() for line in lines if line.startswith("## ")]
    return AtsReport(
        keyword_coverage=score,
        missing_skills=missing,
        has_standard_headings=all(h in headings for h in STANDARD_HEADINGS),
        line_count=len(lines),
    )
