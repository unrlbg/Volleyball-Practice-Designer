from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree

import pytest

from app.services.assets import AssetRegistry

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"


def asset_path(asset: dict) -> Path:
    return STATIC / asset["asset"].removeprefix("/static/")


@pytest.fixture(scope="module")
def registry() -> AssetRegistry:
    return AssetRegistry(MANIFEST)


def test_asset_manifest_loads(registry):
    assert registry.schema_version == 6
    assert len(registry.assets) >= 200
    assert len(registry.by_id) == len(registry.assets)


def test_asset_api_loads(client):
    response = client.get("/api/assets")
    assert response.status_code == 200
    assert response.json()["schemaVersion"] == 6
    assert len(response.json()["assets"]) >= 200


@pytest.mark.parametrize(
    ("role", "expected_per_team"),
    [
        ("generic", 4),
        ("setter", 8),
        ("libero", 8),
        ("middle", 9),
        ("outside", 11),
        ("opposite", 10),
    ],
)
def test_every_required_role_has_both_team_pose_libraries(registry, role, expected_per_team):
    for team in ("A", "B"):
        assets = [a for a in registry.assets if a.get("category") == "player" and a.get("role") == role and a.get("team") == team and a.get("visualStyle") == "legacy_vector"]
        assert len(assets) == expected_per_team
        assert all(a["asset"].endswith(".svg") for a in assets)


def test_every_required_setter_pose_exists_for_both_teams(registry):
    required = {
        "Ready",
        "Front Set",
        "Back Set",
        "Jump Set",
        "One-Hand Set",
        "Setter Dump",
        "Defensive Position",
        "Transition",
    }
    for team in ("A", "B"):
        poses = {a["pose"] for a in registry.assets if a.get("role") == "setter" and a.get("team") == team and a.get("visualStyle") == "legacy_vector"}
        assert poses == required


def test_coach_has_seven_neutral_poses(registry):
    coaches = [a for a in registry.assets if a.get("category") == "player" and a.get("role") == "coach" and a.get("visualStyle") == "legacy_vector"]
    assert len(coaches) == 7
    assert {a["team"] for a in coaches} == {"Neutral"}


def test_libero_uniform_assets_differ_from_regular_uniforms(registry):
    libero = registry.resolve_player("A", "Libero", "Reception")
    setter = registry.resolve_player("A", "Setter", "Ready")
    assert libero["uniform"] == "burnt_orange_cream_libero"
    assert libero["uniform"] != setter["uniform"]
    assert libero["asset"] != setter["asset"]


def test_four_ball_cart_variants_exist(registry):
    carts = [a for a in registry.assets if a.get("equipmentType") == "ball_cart"]
    assert {a["id"] for a in carts} == {
        "ball_cart_blue",
        "ball_cart_black",
        "compact_ball_cart",
        "folding_ball_cart",
    }


def test_ball_cart_resolves_to_cart_not_ball(registry):
    cart = registry.resolve_equipment("Ball Cart")
    assert cart["id"] == "ball_cart_blue"
    assert cart["category"] == "equipment"
    assert cart["equipmentType"] == "ball_cart"
    source = asset_path(cart).read_text(encoding="utf-8")
    assert 'viewBox="0 0 120 150"' in source
    assert source.count("<circle") >= 3


def test_original_ball_assets_resolve_without_branding(registry):
    for label, expected in [("Ball", "single_ball"), ("Ball Group", "ball_group"), ("Ball Pile", "ball_pile")]:
        asset = registry.resolve_equipment(label)
        assert asset["id"] == expected
        source = asset_path(asset).read_text(encoding="utf-8").lower()
        assert "mikasa" not in source
        assert "#165fa1" in source
        assert "#f1ca34" in source


def test_old_schematic_player_migrates_safely(registry):
    old = {"id": "p1", "type": "player", "label": "Setter", "role": "Setter", "pose": "Front set", "team": "B", "x": 430, "y": 510}
    migrated = registry.migrate_object(old)
    assert migrated["assetId"] == "professional_team_b_female_athlete_01_front_set"
    assert migrated["visualStyle"] == "professional"
    assert migrated["x"] == 430 and migrated["y"] == 510
    assert migrated["anchor"] == {"x": 0.5, "y": 1.0}


def test_old_ball_cart_and_ball_migrate_safely(registry):
    cart = registry.migrate_object({"id": "c1", "type": "equipment", "label": "Ball cart"})
    ball = registry.migrate_object({"id": "b1", "type": "equipment", "label": "Ball"})
    assert cart["assetId"] == "ball_cart_blue"
    assert ball["assetId"] == "single_ball"


def test_missing_asset_falls_back_safely(registry):
    missing = registry.migrate_object({"id": "x", "type": "equipment", "label": "Unknown future machine", "assetId": "gone"})
    assert missing["assetId"] == "safe_fallback"
    assert registry.by_id[missing["assetId"]]["asset"].endswith("fallback.svg")


def test_pose_change_resolution_preserves_transform_properties(registry):
    source = {
        "id": "p",
        "type": "player",
        "role": "Setter",
        "pose": "Ready",
        "team": "A",
        "x": 321,
        "y": 456,
        "scale": 1.35,
        "rotation": 27,
        "locked": True,
        "mirror": True,
        "layer": 6,
    }
    changed = deepcopy(source)
    changed["pose"] = "Jump Set"
    migrated = registry.migrate_object(changed)
    assert migrated["assetId"] == "professional_female_athlete_01_ready"
    assert migrated["pose"] == "Ready"
    for field in ("x", "y", "scale", "rotation", "locked", "mirror", "layer"):
        assert migrated[field] == source[field]


def test_assets_remain_after_save_and_load(client):
    payload = {
        "metadata": {"name": "Asset persistence"},
        "frames": [
            {
                "id": "frame-one",
                "name": "Frame 1",
                "court": {},
                "objects": [
                    {"id": "p", "type": "player", "role": "Outside", "pose": "Jump Attack", "team": "A", "assetId": "a_outside_jump_attack"},
                    {"id": "c", "type": "equipment", "label": "Folding Ball Cart", "assetId": "folding_ball_cart"},
                ],
            }
        ],
    }
    saved = client.post("/api/drills", json=payload)
    assert saved.status_code == 201
    loaded = client.get(f'/api/drills/{saved.json()["id"]}').json()
    assert [o["assetId"] for o in loaded["frames"][0]["objects"]] == ["professional_female_athlete_02_jump_attack", "folding_ball_cart"]


def test_assets_are_independent_after_frame_copy(registry):
    original = {"id": "f1", "objects": [registry.migrate_object({"id": "p1", "type": "player", "role": "Middle", "pose": "Block Ready", "team": "B"})]}
    duplicate = deepcopy(original)
    duplicate["id"] = "f2"
    duplicate["objects"][0]["id"] = "p2"
    duplicate["objects"][0]["assetId"] = "b_middle_quick_attack"
    assert original["objects"][0]["assetId"] == "professional_team_b_female_athlete_03_block_ready"
    assert duplicate["objects"][0]["assetId"] == "b_middle_quick_attack"


def test_every_manifest_svg_exists_and_is_valid(registry):
    for asset in [item for item in registry.assets if item["asset"].endswith(".svg")]:
        path = asset_path(asset)
        assert path.is_file(), asset["id"]
        root = ElementTree.fromstring(path.read_text(encoding="utf-8"))
        assert root.tag.endswith("svg")


def test_no_external_runtime_image_url_is_required(registry):
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    assert '"asset": "http' not in manifest_text
    for asset in [item for item in registry.assets if item["asset"].endswith(".svg")]:
        source = asset_path(asset).read_text(encoding="utf-8").lower()
        assert "href=\"http" not in source
        assert "url(http" not in source


def test_png_export_waits_and_inlines_assets():
    source = (ROOT / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert "await Promise.all(images.map" in source
    assert "data:image/svg+xml" in source
    assert "PNG exported: ${mode}" in source
    assert "readAsDataURL" in source


def test_migration_performance_for_24_objects_across_frames(registry):
    objects = [
        {"id": f"p{i}", "type": "player", "role": "Setter", "pose": "Front Set", "team": "A", "x": i * 10, "y": 300}
        for i in range(24)
    ]
    drill = {"frames": [{"id": f"f{frame}", "objects": deepcopy(objects)} for frame in range(4)]}
    start = time.perf_counter()
    migrated = registry.migrate_drill(drill)
    elapsed = time.perf_counter() - start
    assert sum(len(frame["objects"]) for frame in migrated["frames"]) == 96
    assert all(obj["assetId"] == "professional_female_athlete_01_front_set" for frame in migrated["frames"] for obj in frame["objects"])
    assert elapsed < 0.25


def test_manifest_contains_only_stable_unique_ids(registry):
    ids = [asset["id"] for asset in registry.assets]
    assert len(ids) == len(set(ids))
    assert all(asset_id == asset_id.lower() and " " not in asset_id for asset_id in ids)
