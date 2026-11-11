"""System prompts, ported from cv-tailor/src/prompts.ts.

PARSE_SYSTEM is verbatim. REWRITE_SYSTEM is verbatim except the "Return JSON" line: bullets are
a list of {"id", "text"} instead of an id -> text map (see models.RewriteOutput).
"""

PARSE_SYSTEM = """Extract structured data from a job description.
Return JSON: {"role": string, "seniority": string, "requiredSkills": string[], "niceToHave": string[]}.
Use the exact wording of skills as they appear in the job description.
Include only skills that are explicitly stated."""

REWRITE_SYSTEM = """You rewrite CV content for a target job.
Rules:
- Use ONLY facts present in the input. Never add skills, tools, numbers, employers or dates that are not in the input.
- Start each bullet with a past-tense action verb. Maximum 35 words per bullet.
- Mirror the job's terminology only where the facts support it.
Return JSON: {"summary": string (maximum 2 sentences, built from summaryFacts only), "bullets": [{"id": "<achievement id>", "text": string}]}."""
