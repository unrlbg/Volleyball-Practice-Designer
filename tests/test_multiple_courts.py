from __future__ import annotations

import time
from copy import deepcopy
from pathlib import Path

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app" / "static" / "assets" / "manifest.json"


def court(court_id: str, name: str, x: int, y: int, width: int = 720, **settings):
    return {
        "id": court_id,
        "type": "court",
        "name": name,
        "x": x,
        "y": y,
        "width": width,
        "height": width / 2,
        "rotation": 0,
        "locked": False,
        "style": "competition",
        "settings": {
            "showAttackLines": settings.get("attack", True),
            "showZoneLabels": settings.get("zones", True),
            "showNet": settings.get("net", True),
            "showGrid": settings.get("grid", False),
            "showAntennas": settings.get("antennas", True),
        },
    }


def multi_court_drill():
    courts = [
        court("court-1", "Serve Court", 480, 360, attack=True),
        court("court-2", "Defense Court", 1280, 360, attack=False, grid=True),
        court("court-3", "Transition Court", 880, 820, width=640, zones=False),
    ]
    objects = [
        {"id": f"player-{index}", "type": "player", "role": "Setter", "pose": "Ready", "team": "A", "courtId": courts[index % 3]["id"], "x": 300 + index * 20, "y": 300}
        for index in range(12)
    ]
    return {
        "schema_version": 2,
        "metadata": {"name": "Three courts"},
        "frames": [{"id": "frame-1", "name": "Frame 1", "courts": courts, "objects": objects}],
    }


def test_old_single_court_migrates_to_selectable_court(client):
    payload = {
        "schema_version": 1,
        "metadata": {"name": "Legacy court"},
        "court": {"attackLines": False, "zones": True, "grid": True, "net": True, "antennas": False},
        "frames": [{"id": "f", "name": "Frame 1", "objects": [{"id": "p", "type": "player", "role": "Setter", "pose": "Ready", "team": "A"}]}],
    }
    saved = client.post("/api/drills", json=payload).json()
    frame = saved["frames"][0]
    assert saved["schema_version"] == 3
    assert len(frame["courts"]) == 1
    assert frame["courts"][0]["type"] == "court"
    assert frame["courts"][0]["settings"]["showAttackLines"] is False
    assert frame["courts"][0]["settings"]["showGrid"] is True
    assert frame["objects"][0]["courtId"] == frame["courts"][0]["id"]


def test_three_courts_save_and_reload_independently(client):
    payload = multi_court_drill()
    created = client.post("/api/drills", json=payload)
    assert created.status_code == 201
    loaded = client.get(f'/api/drills/{created.json()["id"]}').json()
    courts = loaded["frames"][0]["courts"]
    assert [item["name"] for item in courts] == ["Serve Court", "Defense Court", "Transition Court"]
    assert [(item["x"], item["y"]) for item in courts] == [(480, 360), (1280, 360), (880, 820)]
    assert courts[0]["settings"]["showAttackLines"] is True
    assert courts[1]["settings"]["showAttackLines"] is False
    assert courts[1]["settings"]["showGrid"] is True
    assert courts[2]["settings"]["showZoneLabels"] is False
    assert all(item["height"] == item["width"] / 2 for item in courts)
    assert {obj["courtId"] for obj in loaded["frames"][0]["objects"]} == {"court-1", "court-2", "court-3"}


def test_duplicate_court_with_contents_is_deep_and_reidentified():
    source = multi_court_drill()["frames"][0]
    source_court = source["courts"][0]
    copied_court = {**deepcopy(source_court), "id": "court-copy", "name": "Serve Court Copy", "x": source_court["x"] + 70}
    copied = [
        {**deepcopy(obj), "id": f'{obj["id"]}-copy', "courtId": copied_court["id"], "x": obj["x"] + 70}
        for obj in source["objects"]
        if obj["courtId"] == source_court["id"]
    ]
    assert copied_court["id"] != source_court["id"]
    assert len(copied) == 4
    assert {item["courtId"] for item in copied} == {"court-copy"}
    assert not ({item["id"] for item in copied} & {item["id"] for item in source["objects"]})
    copied[0]["pose"] = "Jump Set"
    assert source["objects"][0]["pose"] == "Ready"


def test_multiple_court_ui_contract_and_export_modes():
    html = (ROOT / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    source = (ROOT / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    for control in (
        "add-court",
        "duplicate-court",
        "duplicate-court-contents",
        "delete-court",
        "fit-view",
        "arrange-courts",
        "lock-court",
    ):
        assert f'id="{control}"' in html
    for template in ("horizontal2", "vertical2", "horizontal3", "twoPlusOne", "stations"):
        assert f'value="{template}"' in html
        assert template in source
    for mode in ("selected", "all", "viewport", "workspace"):
        assert f'value="{mode}"' in html
    assert "interaction.object.height = interaction.object.width / COURT_RATIO" in source
    assert "Court and contents duplicated" in source
    assert "workspaceBounds" in source and "fitAll" in source


def test_experimental_player_review_assets_are_local_and_complete():
    registry = AssetRegistry(MANIFEST)
    assets = [asset for asset in registry.assets if asset.get("category") == "experimental_player"]
    assert len(assets) == 36
    assert {asset["style"] for asset in assets} == {"style_a", "style_b", "style_c"}
    assert all(asset["experimental"] is True for asset in assets)
    assert all(asset["asset"].endswith(".webp") and asset["source"].endswith(".png") for asset in assets)
    assert all((ROOT / "app" / "static" / asset["asset"].removeprefix("/static/")).is_file() for asset in assets)
    for style in ("style_a", "style_b", "style_c"):
        poses = {asset["poseKey"] for asset in assets if asset["style"] == style}
        assert {"ready", "front_set", "back_set", "jump_set", "jump_attack", "single_block", "reception", "dig", "dive", "holding_ball"} <= poses


def test_fifty_object_three_court_migration_performance():
    registry = AssetRegistry(MANIFEST)
    payload = multi_court_drill()
    frame = payload["frames"][0]
    frame["objects"] = [
        {"id": f"p-{index}", "type": "player", "role": "Setter", "pose": "Front Set", "team": "A", "courtId": frame["courts"][index % 3]["id"], "x": index * 24, "y": 300}
        for index in range(54)
    ]
    start = time.perf_counter()
    migrated = registry.migrate_drill(payload)
    elapsed = time.perf_counter() - start
    assert len(migrated["frames"][0]["objects"]) == 54
    assert len(migrated["frames"][0]["courts"]) == 3
    assert elapsed < 0.25
