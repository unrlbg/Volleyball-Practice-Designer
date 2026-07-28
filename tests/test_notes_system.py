from copy import deepcopy
from uuid import uuid4

from app.models.notes import default_drill_notes
from tests.test_api import drill_payload


def note_item(text: str, order: int):
    return {"id": str(uuid4()), "text": text, "completed": False, "order": order}


def test_empty_notes_structure_is_created_safely(client):
    payload = drill_payload()
    payload.pop("notes", None)
    created = client.post("/api/drills", json=payload).json()
    assert created["notes"]["formatVersion"] == 1
    assert created["notes"]["generalComments"] == ""
    assert created["notes"]["coachingPoints"] == []


def test_drill_notes_save_and_reload(client):
    payload = drill_payload()
    payload["notes"] = default_drill_notes()
    payload["notes"]["description"] = "Train setter release tempo"
    payload["notes"]["generalComments"] = "Works better with two setters"
    payload["notes"]["coachingPoints"] = [
        note_item("Setter stops before contact", 0),
        note_item("Outside starts after setter release", 1),
        note_item("Middle holds the blocker", 2),
    ]
    drill_id = client.post("/api/drills", json=payload).json()["id"]
    loaded = client.get(f"/api/drills/{drill_id}").json()
    assert loaded["notes"]["description"] == "Train setter release tempo"
    assert loaded["notes"]["generalComments"] == "Works better with two setters"
    assert [x["text"] for x in loaded["notes"]["coachingPoints"]] == [
        "Setter stops before contact",
        "Outside starts after setter release",
        "Middle holds the blocker",
    ]


def test_structured_note_sections_preserve_order(client):
    payload = drill_payload()
    payload["notes"] = default_drill_notes()
    for section in ["commonMistakes", "progressions", "regressions", "variations"]:
        payload["notes"][section] = [note_item(f"{section} second", 1), note_item(f"{section} first", 0)]
    drill_id = client.post("/api/drills", json=payload).json()["id"]
    loaded = client.get(f"/api/drills/{drill_id}").json()
    for section in ["commonMistakes", "progressions", "regressions", "variations"]:
        assert [x["text"] for x in loaded["notes"][section]] == [f"{section} first", f"{section} second"]


def test_old_generic_notes_migrate_to_general_comments(client):
    payload = drill_payload()
    payload["metadata"]["notes"] = "Use only after players understand base positions"
    drill_id = client.post("/api/drills", json=payload).json()["id"]
    loaded = client.get(f"/api/drills/{drill_id}").json()
    assert loaded["notes"]["generalComments"] == "Use only after players understand base positions"


def test_malformed_notes_data_is_handled_safely(client):
    payload = drill_payload()
    payload["notes"] = {"coachingPoints": "bad", "generalComments": ["bad"]}
    created = client.post("/api/drills", json=payload)
    assert created.status_code == 201
    notes = created.json()["notes"]
    assert notes["generalComments"] == ""
    assert notes["coachingPoints"] == []


def test_practice_notes_save_and_reload(client):
    payload = {
        "name": "Tuesday session",
        "main_objective": "Side-out",
        "practiceNotes": {
            "mainObjective": "Win first-ball side-out",
            "technicalObjective": "Stable platform",
            "tacticalObjective": "Attack seams",
            "physicalObjective": "High tempo",
            "intensity": "High",
            "importantNotes": "Limit jumps for middles",
            "generalComments": "Start with short court",
            "postPracticeReview": "Passing improved",
            "formatVersion": 1,
        },
        "sections": [{"name": "Practice plan", "drills": []}],
    }
    practice_id = client.post("/api/practices", json=payload).json()["id"]
    loaded = client.get(f"/api/practices/{practice_id}").json()
    assert loaded["practiceNotes"]["mainObjective"] == "Win first-ball side-out"
    assert loaded["practiceNotes"]["importantNotes"] == "Limit jumps for middles"


def test_sticky_note_and_object_note_save_reload_and_duplicate(client):
    payload = drill_payload()
    setter = payload["frames"][0]["objects"][0]
    setter["note"] = {"text": "Release earlier", "showIndicator": True, "showInExport": False}
    payload["frames"][0]["objects"].append(
        {
            "id": str(uuid4()),
            "type": "sticky-note",
            "label": "Sticky Note",
            "text": "Rotate after five balls",
            "x": 800,
            "y": 500,
            "width": 220,
            "height": 120,
            "rotation": 8,
            "opacity": 0.85,
            "backgroundColor": "#fff4a6",
            "textSize": 16,
        }
    )
    drill_id = client.post("/api/drills", json=payload).json()["id"]
    loaded = client.get(f"/api/drills/{drill_id}").json()
    objects = loaded["frames"][0]["objects"]
    assert any(o["type"] == "sticky-note" and o["text"] == "Rotate after five balls" for o in objects)
    assert objects[0]["note"]["text"] == "Release earlier"
    copy = client.post(f"/api/drills/{drill_id}/duplicate").json()
    assert copy["id"] != drill_id
    assert copy["frames"][0]["objects"][1]["text"] == "Rotate after five balls"
    copy["frames"][0]["objects"][1]["text"] = "Independent note"
    client.put(f'/api/drills/{copy["id"]}', json=copy)
    original = client.get(f"/api/drills/{drill_id}").json()
    assert original["frames"][0]["objects"][1]["text"] == "Rotate after five balls"


def test_search_relevant_note_text_is_returned_to_frontend(client):
    payload = drill_payload()
    payload["notes"] = default_drill_notes()
    payload["notes"]["generalComments"] = "Reduce court width for younger players"
    client.post("/api/drills", json=payload)
    drills = client.get("/api/drills").json()
    assert "Reduce court width" in drills[0]["notes"]["generalComments"]


def test_print_and_shortcut_hooks_exist(client):
    javascript = client.get("/static/js/app.js").text
    assert "drillNotesPrintHtml" in javascript
    assert "INPUT\",\"TEXTAREA\",\"SELECT" in javascript
    assert "note-indicator:not(.export-note)" in javascript


def test_coaching_notes_panel_is_visible_editor_column(client):
    html = client.get("/").text
    css = client.get("/static/css/improvements.css").text
    assert 'class="coaching-notes-panel panel"' in html
    assert 'id="note-description"' in html
    assert 'id="note-generalComments"' in html
    assert 'data-right-tab="notes"' not in html
    assert "grid-template-columns: 210px minmax(430px, 1fr) minmax(380px, 420px) 250px" in css
    assert ".editor-shell.notes-collapsed" in css
