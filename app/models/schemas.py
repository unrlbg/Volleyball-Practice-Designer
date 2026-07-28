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


class NoteItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = ""
    completed: bool = False
    order: int = 0


class DrillNotes(BaseModel):
    description: str = ""
    coachingPoints: list[NoteItem] = Field(default_factory=list)
    commonMistakes: list[NoteItem] = Field(default_factory=list)
    progressions: list[NoteItem] = Field(default_factory=list)
    regressions: list[NoteItem] = Field(default_factory=list)
    variations: list[NoteItem] = Field(default_factory=list)
    equipmentNotes: str = ""
    generalComments: str = ""
    postTrainingObservations: str = ""
    formatVersion: int = 1

    @field_validator("description", "equipmentNotes", "generalComments", "postTrainingObservations", mode="before")
    @classmethod
    def text_fields_are_safe(cls, value: Any) -> str:
        return value if isinstance(value, str) else ""

    @field_validator("coachingPoints", "commonMistakes", "progressions", "regressions", "variations", mode="before")
    @classmethod
    def list_fields_are_safe(cls, value: Any) -> list[Any]:
        return value if isinstance(value, list) else []


class Drill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 2
    metadata: DrillMetadata
    created_at: str = Field(default_factory=utc_now)
    modified_at: str = Field(default_factory=utc_now)
    court: dict[str, Any] = Field(default_factory=dict)
    frames: list[dict[str, Any]] = Field(default_factory=list)
    notes: DrillNotes = Field(default_factory=DrillNotes)
    thumbnail: str | None = None


class PracticeNotes(BaseModel):
    mainObjective: str = ""
    technicalObjective: str = ""
    tacticalObjective: str = ""
    physicalObjective: str = ""
    intensity: str = ""
    importantNotes: str = ""
    generalComments: str = ""
    postPracticeReview: str = ""
    formatVersion: int = 1

    @field_validator("mainObjective", "technicalObjective", "tacticalObjective", "physicalObjective", "intensity", "importantNotes", "generalComments", "postPracticeReview", mode="before")
    @classmethod
    def practice_text_fields_are_safe(cls, value: Any) -> str:
        return value if isinstance(value, str) else ""


class Practice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 1
    name: str
    date: str | None = None
    team: str = ""
    main_objective: str = ""
    notes: str = ""
    practiceNotes: PracticeNotes = Field(default_factory=PracticeNotes)
    sections: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    modified_at: str = Field(default_factory=utc_now)


class PowerPointFrameImage(BaseModel):
    id: str = ""
    name: str = ""
    image: str


class DrillPowerPointExport(BaseModel):
    drill: dict[str, Any]
    frames: list[PowerPointFrameImage]


class PracticePowerPointExport(BaseModel):
    practice: dict[str, Any]
    drills: list[DrillPowerPointExport]


class PlayerFigurePowerPointExport(BaseModel):
    mode: str = "all"
    role: str | None = None
    format: str = "pptx"
    assetIds: list[str] = Field(default_factory=list)
