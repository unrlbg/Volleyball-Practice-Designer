from copy import deepcopy
from uuid import uuid4


def visual_object(kind, label, **extra):
    return {
        "id": str(uuid4()),
        "type": kind,
        "label": label,
        "x": extra.pop("x", 300),
        "y": extra.pop("y", 300),
        "rotation": extra.pop("rotation", 0),
        "scale": extra.pop("scale", 1),
        "opacity": 1,
        "locked": False,
        **extra,
    }


def complete_drill():
    first_objects = [
        visual_object("player", "Setter", role="Setter", pose="Jump set", team="A", x=420),
        visual_object("player", "Libero", role="Libero", pose="Reception", team="B", x=800),
        visual_object("equipment", "Ball", team="Neutral", x=510),
        visual_object("equipment", "Ball", team="Neutral", x=540),
        visual_object("equipment", "Ball cart", team="Neutral", x=150),
        visual_object("equipment", "Target hoop", team="Neutral", x=980),
        visual_object("equipment", "Blocking board", team="Neutral", x=610),
        visual_object("arrow", "Ball trajectory", dx=180, dy=-90, curved=True),
        visual_object("shape", "Responsibility area", width=180, height=130),
        visual_object("text", "Text label", text="Setter releases after pass"),
    ]
    second_objects = deepcopy(first_objects)
    for item in second_objects:
        item["id"] = str(uuid4())
    second_objects[0]["x"] = 470
    return {
        "id": str(uuid4()),
        "schema_version": 1,
        "metadata": {"name": "Complete drill", "objective": "Side-out", "tags": ["Reception", "Setting"]},
        "court": {"attackLines": True, "zones": True, "grid": False, "antennas": True, "net": True},
        "frames": [
            {"id": str(uuid4()), "name": "Start", "court": {"attackLines": True, "zones": True, "net": True}, "objects": first_objects},
            {"id": str(uuid4()), "name": "Finish", "court": {"attackLines": False, "zones": False, "net": True}, "objects": second_objects},
        ],
    }


def save_and_load(client, payload=None):
    payload = payload or complete_drill()
    created = client.post("/api/drills", json=payload)
    assert created.status_code == 201
    return client.get(f'/api/drills/{created.json()["id"]}').json()


def test_schema_version_persists(client):
    assert save_and_load(client)["schema_version"] == 3


def test_frame_ordering_persists(client):
    assert [frame["name"] for frame in save_and_load(client)["frames"]] == ["Start", "Finish"]


def test_court_settings_persist(client):
    assert save_and_load(client)["court"] == {"attackLines": True, "zones": True, "grid": False, "antennas": True, "net": True}


def test_zone_visibility_persists_per_frame(client):
    frames = save_and_load(client)["frames"]
    assert frames[0]["court"]["zones"] is True
    assert frames[1]["court"]["zones"] is False


def test_attack_line_visibility_persists_per_frame(client):
    frames = save_and_load(client)["frames"]
    assert frames[0]["court"]["attackLines"] is True
    assert frames[1]["court"]["attackLines"] is False


def test_multiple_balls_persist(client):
    objects = save_and_load(client)["frames"][0]["objects"]
    assert len([obj for obj in objects if obj["label"] == "Ball"]) == 2


def test_multiple_players_and_teams_persist(client):
    players = [obj for obj in save_and_load(client)["frames"][0]["objects"] if obj["type"] == "character"]
    assert len(players) == 2
    assert {player["team"] for player in players} == {"A", "B"}


def test_player_role_and_pose_persist(client):
    players = [obj for obj in save_and_load(client)["frames"][0]["objects"] if obj["type"] == "character"]
    assert (players[0]["role"], players[0]["pose"]) == ("Setter", "Ready")
    assert (players[1]["role"], players[1]["pose"]) == ("Libero", "Reception")


def test_equipment_target_and_blocking_objects_persist(client):
    labels = {obj["label"] for obj in save_and_load(client)["frames"][0]["objects"]}
    assert {"Ball cart", "Target hoop", "Blocking board"}.issubset(labels)


def test_arrows_shapes_and_text_persist(client):
    types = {obj["type"] for obj in save_and_load(client)["frames"][0]["objects"]}
    assert {"arrow", "shape", "text"}.issubset(types)


def test_layer_order_persists(client):
    source = complete_drill()
    expected = [obj["id"] for obj in source["frames"][0]["objects"]]
    loaded = save_and_load(client, source)
    assert [obj["id"] for obj in loaded["frames"][0]["objects"]] == expected


def test_renamed_drill_persists(client):
    source = complete_drill()
    created = client.post("/api/drills", json=source).json()
    created["metadata"]["name"] = "Renamed drill"
    response = client.put(f'/api/drills/{created["id"]}', json=created)
    assert response.status_code == 200
    assert client.get(f'/api/drills/{created["id"]}').json()["metadata"]["name"] == "Renamed drill"


def test_duplicate_is_deep_independent(client):
    original = client.post("/api/drills", json=complete_drill()).json()
    duplicate = client.post(f'/api/drills/{original["id"]}/duplicate').json()
    duplicate["frames"][0]["objects"][0]["x"] = 999
    client.put(f'/api/drills/{duplicate["id"]}', json=duplicate)
    reloaded_original = client.get(f'/api/drills/{original["id"]}').json()
    assert reloaded_original["frames"][0]["objects"][0]["x"] == 420


def test_saved_drill_can_be_added_to_practice(client):
    drill = client.post("/api/drills", json=complete_drill()).json()
    practice = {
        "name": "Side-out practice",
        "sections": [{"name": "Technical work", "drills": [{"drill_id": drill["id"], "name": drill["metadata"]["name"], "duration": 15}]}],
    }
    saved = client.post("/api/practices", json=practice)
    assert saved.status_code == 201
    loaded = client.get(f'/api/practices/{saved.json()["id"]}').json()
    assert loaded["sections"][0]["drills"][0]["drill_id"] == drill["id"]


def test_malformed_json_is_skipped_in_list_and_safe_on_get(client):
    directory = client.app.state.drills.base_dir
    (directory / "broken.json").write_text("{ definitely not json", encoding="utf-8")
    (directory / "empty.json").write_text("", encoding="utf-8")
    assert client.get("/api/drills").status_code == 200
    assert client.get("/api/drills/broken").status_code == 404
    assert client.get("/api/drills/empty").status_code == 404


def test_missing_data_directories_are_created(client):
    assert client.app.state.drills.base_dir.is_dir()
    assert client.app.state.practices.base_dir.is_dir()
