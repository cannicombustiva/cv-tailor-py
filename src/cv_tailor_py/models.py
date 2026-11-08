"""Pydantic v2 models for the profile and job boundaries.

Field names are snake_case in Python; JSON uses camelCase (matching the TS version).
"""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Model(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
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
