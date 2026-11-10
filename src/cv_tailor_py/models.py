"""Pydantic v2 models for the profile and job boundaries.

Field names are snake_case in Python; JSON uses camelCase (matching the TS version).
Serialization uses the camelCase aliases by default, so Braintrust spans match the TS shape.
"""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Model(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
        extra="forbid",
        frozen=True,
    )


class Achievement(_Model):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    skills: list[str] = Field(default_factory=list)


class Role(_Model):
    company: str = Field(min_length=1)
    title: str = Field(min_length=1)
    start: str
    end: str
    achievements: list[Achievement] = Field(default_factory=list)


class Education(_Model):
    school: str = Field(min_length=1)
    degree: str = Field(min_length=1)
    year: str


class Profile(_Model):
    name: str = Field(min_length=1)
    email: str
    location: str
    summary_facts: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    roles: list[Role] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)


class JobSpec(_Model):
    id: str = Field(min_length=1)
    job_description: str = Field(min_length=1)
    required_skills: list[str] = Field(default_factory=list)


class ParsedJD(_Model):
    """Structured output of the parse_jd step (TS: ParsedJD).

    No defaults: every field is required so the OpenAI strict JSON schema matches exactly.
    """

    role: str
    seniority: str
    required_skills: list[str]
    nice_to_have: list[str]


class Rewritten(_Model):
    """Output of the rewrite_bullets step: summary plus bullet text keyed by achievement id."""

    summary: str
    bullets: dict[str, str]


class RewrittenBullet(_Model):
    id: str
    text: str


class RewriteOutput(_Model):
    """What the LLM returns for rewrite_bullets (wire shape of Rewritten).

    OpenAI strict structured outputs require `additionalProperties: false` on every object,
    so a `dict[str, str]` map cannot be expressed; bullets come back as a list of {id, text}.
    """

    summary: str
    bullets: list[RewrittenBullet]

    def to_rewritten(self) -> Rewritten:
        return Rewritten(summary=self.summary, bullets={b.id: b.text for b in self.bullets})


class AtsReport(_Model):
    keyword_coverage: float
    missing_skills: list[str]
    has_standard_headings: bool
    line_count: int
