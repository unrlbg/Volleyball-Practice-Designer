from uuid import uuid4


def drill_payload(name="Serve receive"):
    return {
        "id": str(uuid4()),
        "schema_version": 1,
        "metadata": {"name": name, "objective": "First contact", "tags": ["Reception"]},
        "court": {"attackLines": True, "zones": True},
        "frames": [
            {
                "id": str(uuid4()),
                "name": "Frame 1",
                "court": {"attackLines": True, "zones": True},
                "objects": [{"id": str(uuid4()), "type": "player", "role": "Libero", "pose": "Reception"}],
            }
        ],
    }


def test_health_and_index(client):
    assert client.get("/api/health").json()["status"] == "ok"
    root = client.get("/")
    assert root.status_code == 200
    assert "Volleyball Practice Designer" in root.text


def test_static_editor_files_load(client):
    css = client.get("/static/css/app.css")
    improvements = client.get("/static/css/improvements.css")
    javascript = client.get("/static/js/app.js")
    assert css.status_code == improvements.status_code == javascript.status_code == 200
    assert "court-svg" in javascript.text
    assert ".editor-shell" in css.text


def test_drill_name_is_required(client):
    payload = drill_payload()
    payload["metadata"]["name"] = "   "
    response = client.post("/api/drills", json=payload)
    assert response.status_code == 422
    assert "Drill name is required" in response.text


def test_generated_drill_ids_are_unique(client):
    first = drill_payload()
    second = drill_payload("Second drill")
    first.pop("id")
    second.pop("id")
    first_id = client.post("/api/drills", json=first).json()["id"]
    second_id = client.post("/api/drills", json=second).json()["id"]
    assert first_id != second_id


def test_drill_crud_persists_complete_frames(client):
    payload = drill_payload()
    created = client.post("/api/drills", json=payload)
    assert created.status_code == 201
    drill_id = created.json()["id"]
    loaded = client.get(f"/api/drills/{drill_id}")
    assert loaded.status_code == 200
    assert loaded.json()["frames"][0]["objects"][0]["role"] == "Libero"
    payload["metadata"]["name"] = "Updated reception"
    assert client.put(f"/api/drills/{drill_id}", json=payload).json()["metadata"]["name"] == "Updated reception"
    assert len(client.get("/api/drills").json()) == 1
    assert client.delete(f"/api/drills/{drill_id}").status_code == 204
    assert client.get(f"/api/drills/{drill_id}").status_code == 404


def test_duplicate_drill_is_independent(client):
    payload = drill_payload()
    drill_id = client.post("/api/drills", json=payload).json()["id"]
    copy = client.post(f"/api/drills/{drill_id}/duplicate").json()
    assert copy["id"] != drill_id
    assert copy["frames"][0]["id"] == payload["frames"][0]["id"]
    assert copy["frames"][0]["objects"][0]["assetId"] == "professional_female_athlete_04_reception"
    copy["frames"][0]["objects"][0]["pose"] = "Dig"
    client.put(f'/api/drills/{copy["id"]}', json=copy)
    assert client.get(f"/api/drills/{drill_id}").json()["frames"][0]["objects"][0]["pose"] == "Reception"


def test_practice_crud(client):
    payload = {
        "name": "Tuesday session",
        "main_objective": "Side-out",
        "sections": [{"name": "Technical work", "drills": [{"name": "Serve receive", "duration": 15}]}],
    }
    created = client.post("/api/practices", json=payload)
    assert created.status_code == 201
    practice_id = created.json()["id"]
    assert client.get(f"/api/practices/{practice_id}").json()["sections"][0]["drills"][0]["duration"] == 15
    copy = client.post(f"/api/practices/{practice_id}/duplicate")
    assert copy.status_code == 201
    assert copy.json()["id"] != practice_id


def test_invalid_document_id_is_controlled(client):
    response = client.get("/api/drills/not$valid")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid item id"
