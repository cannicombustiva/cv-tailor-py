"""Pipeline steps, ported from cv-tailor/src/agent.ts. Each step is a Braintrust span.

Not ported yet: cv_agent.
"""

import json

from braintrust import current_span, traced

from cv_tailor_py import llm
from cv_tailor_py.ats import run_ats_checks
from cv_tailor_py.models import AtsReport, ParsedJD, Profile, RewriteOutput, Rewritten, Role
from cv_tailor_py.prompts import PARSE_SYSTEM, REWRITE_SYSTEM


# Step 1: LLM extracts what the job asks for.
@traced(name="parse_jd")
def parse_jd(job_description: str) -> ParsedJD:
    return llm.structured_call(PARSE_SYSTEM, job_description, ParsedJD)


# Step 2: plain code, no LLM. Keeps the achievements that overlap most with the job.
@traced(name="match_profile")
def match_profile(profile: Profile, jd: ParsedJD, per_role: int = 5) -> list[Role]:
    wanted = {s.lower() for s in [*jd.required_skills, *jd.nice_to_have]}

    def score(skills: list[str]) -> int:
        # Counts duplicates, like the TS filter().length.
        return sum(1 for s in skills if s.lower() in wanted)

    def top(role: Role) -> Role:
        # sorted() is stable, so ties keep profile order (TS: Array.prototype.sort is stable too).
        ranked = sorted(role.achievements, key=lambda a: -score(a.skills))
        return role.model_copy(update={"achievements": ranked[:per_role]})

    return [top(role) for role in profile.roles]


def rewrite_input(profile: Profile, roles: list[Role], jd: ParsedJD) -> str:
    """User message for rewrite_bullets: the target JD plus only the selected facts.

    Byte-identical to the TS `JSON.stringify({ target: jd, facts })`.
    """
    facts = {
        "summaryFacts": profile.summary_facts,
        "achievements": [{"id": a.id, "text": a.text} for r in roles for a in r.achievements],
    }
    return json.dumps(
        {"target": jd.model_dump(mode="json"), "facts": facts},
        separators=(",", ":"),
        ensure_ascii=False,
    )


# Step 3: LLM rewrites only the selected facts.
@traced(name="rewrite_bullets")
def rewrite_bullets(profile: Profile, roles: list[Role], jd: ParsedJD) -> Rewritten:
    out = llm.structured_call(REWRITE_SYSTEM, rewrite_input(profile, roles, jd), RewriteOutput)
    return out.to_rewritten()


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
