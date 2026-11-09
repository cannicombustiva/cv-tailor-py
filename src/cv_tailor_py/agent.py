"""Pipeline steps, ported from cv-tailor/src/agent.ts. Each step is a Braintrust span.

Not ported yet: match_profile, rewrite_bullets, cv_agent.
"""

from braintrust import current_span, traced

from cv_tailor_py import llm
from cv_tailor_py.ats import run_ats_checks
from cv_tailor_py.models import AtsReport, ParsedJD, Profile, Rewritten, Role
from cv_tailor_py.prompts import PARSE_SYSTEM


# Step 1: LLM extracts what the job asks for.
@traced(name="parse_jd")
def parse_jd(job_description: str) -> ParsedJD:
    return llm.structured_call(PARSE_SYSTEM, job_description, ParsedJD)


# Step 4: deterministic, single column, standard headings.
@traced(name="render")
def render(profile: Profile, roles: list[Role], text: Rewritten, jd: ParsedJD) -> str:
    required = {s.lower() for s in jd.required_skills}
    # Stable sort, required skills first (TS: Array.prototype.sort is stable too).
    skills = sorted(profile.skills, key=lambda s: s.lower() not in required)
    lines = [
        f"# {profile.name}",
        f"{profile.email} | {profile.location}",
        "",
        "## Summary",
        text.summary,
        "",
        "## Experience",
    ]
    for r in roles:
        lines.append(f"### {r.title}, {r.company} ({r.start} - {r.end})")
        for a in r.achievements:
            lines.append(f"- {text.bullets.get(a.id, a.text)}")
        lines.append("")
    lines += ["## Skills", ", ".join(skills), "", "## Education"]
    for e in profile.education:
        lines.append(f"{e.degree}, {e.school}{f' ({e.year})' if e.year else ''}")
    cv = "\n".join(lines)
    bullets = sum(1 for line in lines if line.startswith("- "))
    current_span().log(metrics={"bullets": bullets, "cv_chars": len(cv)})
    return cv


# Step 5: ATS heuristics. The report is attached to the span so it is searchable in Logs.
@traced(name="ats_check")
def ats_check(cv: str, jd: ParsedJD) -> AtsReport:
    report = run_ats_checks(cv, jd)
    current_span().log(metadata={"ats": report.model_dump(by_alias=True)})
    return report
