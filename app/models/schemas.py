from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DrillMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1, max_length=200)
    objective: str = ""
    tags: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Drill name is required")
        return value


class Drill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 2
    metadata: DrillMetadata
    created_at: str = Field(default_factory=utc_now)
    modified_at: str = Field(default_factory=utc_now)
    court: dict[str, Any] = Field(default_factory=dict)
    frames: list[dict[str, Any]] = Field(default_factory=list)
    thumbnail: str | None = None


class Practice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 1
    name: str
    date: str | None = None
    team: str = ""
    main_objective: str = ""
    notes: str = ""
    sections: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    modified_at: str = Field(default_factory=utc_now)
