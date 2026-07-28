from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree
from zipfile import ZipFile


PNG_DATA_URL = (
    "data:image/png;base64,"
    + base64.b64encode(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
    ).decode("ascii")
)


def drill_payload(name="Serve receive", frame_count=2):
    return {
        "id": str(uuid4()),
        "schema_version": 4,
        "metadata": {"name": name, "objective": "First contact", "tags": ["Reception"]},
        "notes": {
            "description": "Pass from zone five into target.",
            "coachingPoints": [{"text": "Platform early", "order": 0}],
            "generalComments": "Keep tempo realistic.",
            "equipmentNotes": "Use two ball carts.",
        },
        "frames": [{"id": str(uuid4()), "name": f"Frame {index + 1}", "objects": []} for index in range(frame_count)],
    }


def frame_images(count=2):
    return [{"id": str(uuid4()), "name": f"Frame {index + 1}", "image": PNG_DATA_URL} for index in range(count)]


def deck_text(path: Path) -> str:
    with ZipFile(path) as pptx:
        text = []
        for name in pptx.namelist():
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                root = ElementTree.fromstring(pptx.read(name))
                text.extend(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
        return "\n".join(text)


def slide_count(path: Path) -> int:
    with ZipFile(path) as pptx:
        return sum(1 for name in pptx.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))


def image_count(path: Path) -> int:
    with ZipFile(path) as pptx:
        return sum(1 for name in pptx.namelist() if name.startswith("ppt/media/image") and name.endswith(".png"))


def test_drill_pptx_file_is_created_with_correct_slide_count_and_notes(client):
    payload = {"drill": drill_payload(), "frames": frame_images(2)}
    response = client.post("/api/exports/powerpoint/drill", json=payload)
    assert response.status_code == 200
    path = Path(response.json()["path"])
    assert path.exists()
    assert slide_count(path) == 2
    text = deck_text(path)
    assert "Serve receive" in text
    assert "Pass from zone five into target." in text
    assert "Platform early" in text
    assert "Keep tempo realistic." in text
    assert "Use two ball carts." in text


def test_frame_images_are_included_and_editor_ui_is_not(client):
    response = client.post("/api/exports/powerpoint/drill", json={"drill": drill_payload(), "frames": frame_images(1)})
    path = Path(response.json()["path"])
    assert image_count(path) == 1
    assert "Export PNG" not in deck_text(path)
    assert "Properties" not in deck_text(path)


def test_practice_pptx_includes_title_overview_section_frames_and_practice_notes(client):
    drill = drill_payload("Side-out wave", 2)
    practice = {
        "id": str(uuid4()),
        "name": "Tuesday practice",
        "date": "2026-07-22",
        "team": "Senior Women",
        "main_objective": "Side-out focus",
        "practiceNotes": {"mainObjective": "Win first-ball side-out", "importantNotes": "Manage workload"},
        "sections": [{"name": "Technical work", "drills": [{"drill_id": drill["id"], "duration": 20}]}],
    }
    response = client.post("/api/exports/powerpoint/practice", json={"practice": practice, "drills": [{"drill": drill, "frames": frame_images(2)}]})
    assert response.status_code == 200
    path = Path(response.json()["path"])
    assert slide_count(path) == 5
    text = deck_text(path)
    assert "Tuesday practice" in text
    assert "Practice Overview" in text
    assert "Technical work" in text
    assert "Win first-ball side-out" in text
    assert "Manage workload" in text


def test_invalid_drill_id_returns_controlled_error(client):
    response = client.post("/api/drills/not$valid/export-powerpoint", json={"drill": drill_payload(), "frames": frame_images(1)})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid item id"
