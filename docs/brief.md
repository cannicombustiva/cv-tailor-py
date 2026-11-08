# cv-tailor-py brief

Python port of cv-tailor (TypeScript). Goal: same pipeline, same Braintrust spans,
then replace `match_profile` (skill overlap) with retrieval, evaluated
keyword vs embedding vs hybrid.

## Hard constraints
- Python 3.13, uv, src layout, Pydantic v2 for every boundary (profile, JD, LLM output)
- mypy strict on src/, ruff with default rules + isort
- Every pipeline step is a `@traced` span; OpenAI client always via `wrap_openai`
- The LLM never sees facts outside the profile (faithfulness invariant)
- Port parity: scores on data/jobs.example.json within ±0.05 of the TS version

## Out of scope for sprint 1
Agents, tool use, MCP, web UI.

## Workflow
One issue per step, one PR per issue, tests in the same PR.