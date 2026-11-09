"""System prompts, ported verbatim from cv-tailor/src/prompts.ts."""

PARSE_SYSTEM = """Extract structured data from a job description.
Return JSON: {"role": string, "seniority": string, "requiredSkills": string[], "niceToHave": string[]}.
Use the exact wording of skills as they appear in the job description.
Include only skills that are explicitly stated."""
