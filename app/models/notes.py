from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4


STRUCTURED_NOTE_SECTIONS = (
    "coachingPoints",
    "commonMistakes",
    "progressions",
    "regressions",
    "variations",
)


def default_note_item(text: str = "", order: int = 0, completed: bool = False) -> dict[str, Any]:
    return {"id": str(uuid4()), "text": text, "completed": completed, "order": order}


def default_drill_notes() -> dict[str, Any]:
    return {
        "description": "",
        "coachingPoints": [],
        "commonMistakes": [],
        "progressions": [],
        "regressions": [],
        "variations": [],
        "equipmentNotes": "",
        "generalComments": "",
        "postTrainingObservations": "",
        "formatVersion": 1,
    }


def default_practice_notes() -> dict[str, Any]:
    return {
        "mainObjective": "",
        "technicalObjective": "",
        "tacticalObjective": "",
        "physicalObjective": "",
        "intensity": "",
        "importantNotes": "",
        "generalComments": "",
        "postPracticeReview": "",
        "formatVersion": 1,
    }


def default_object_note() -> dict[str, Any]:
    return {"text": "", "showIndicator": True, "showInExport": False}


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def normalize_note_item(value: Any, order: int) -> dict[str, Any] | None:
    if isinstance(value, str):
        text = value.strip()
        return default_note_item(text, order) if text else None
    if not isinstance(value, dict):
        return None
    text = _text(value.get("text")).strip()
    if not text:
        return None
    raw_order = value.get("order", order)
    return {
        "id": _text(value.get("id")) or str(uuid4()),
        "text": text,
        "completed": bool(value.get("completed", False)),
        "order": int(raw_order) if isinstance(raw_order, (int, float)) else order,
    }


def normalize_drill_notes(source: Any, legacy: dict[str, Any] | None = None) -> dict[str, Any]:
    notes = default_drill_notes()
    raw = source if isinstance(source, dict) else {}
    legacy = legacy or {}
    notes["description"] = _text(raw.get("description"))
    notes["equipmentNotes"] = _text(raw.get("equipmentNotes"))
    notes["generalComments"] = _text(raw.get("generalComments"))
    notes["postTrainingObservations"] = _text(raw.get("postTrainingObservations"))

    if not notes["generalComments"]:
        notes["generalComments"] = _text(legacy.get("notes") or legacy.get("comments"))
    if not notes["equipmentNotes"]:
        notes["equipmentNotes"] = _text(legacy.get("equipment"))

    legacy_structured = {
        "coachingPoints": legacy.get("coaching"),
        "commonMistakes": legacy.get("mistakes"),
    }
    for section in STRUCTURED_NOTE_SECTIONS:
        values = raw.get(section)
        if not isinstance(values, list):
            values = []
            legacy_value = legacy_structured.get(section)
            if isinstance(legacy_value, str) and legacy_value.strip():
                values = [line.strip() for line in legacy_value.splitlines() if line.strip()]
        normalized = [item for idx, value in enumerate(values) if (item := normalize_note_item(value, idx))]
        normalized.sort(key=lambda item: item["order"])
        for idx, item in enumerate(normalized):
            item["order"] = idx
        notes[section] = normalized
    return notes


def normalize_practice_notes(source: Any, legacy: dict[str, Any] | None = None) -> dict[str, Any]:
    notes = default_practice_notes()
    raw = source if isinstance(source, dict) else {}
    legacy = legacy or {}
    for key in notes:
        if key != "formatVersion":
            notes[key] = _text(raw.get(key))
    if not notes["mainObjective"]:
        notes["mainObjective"] = _text(legacy.get("main_objective"))
    if not notes["generalComments"]:
        notes["generalComments"] = _text(legacy.get("notes"))
    return notes


def normalize_object_note(source: Any) -> dict[str, Any]:
    raw = source if isinstance(source, dict) else {}
    note = default_object_note()
    note["text"] = _text(raw.get("text"))
    note["showIndicator"] = raw.get("showIndicator", True) is not False
    note["showInExport"] = bool(raw.get("showInExport", False))
    return note


def migrate_drill_document(source: dict[str, Any]) -> dict[str, Any]:
    drill = deepcopy(source)
    drill["notes"] = normalize_drill_notes(drill.get("notes"), drill.get("metadata", {}))
    return drill


def migrate_practice_document(source: dict[str, Any]) -> dict[str, Any]:
    practice = deepcopy(source)
    practice["practiceNotes"] = normalize_practice_notes(practice.get("practiceNotes"), practice)
    return practice
