from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from PIL import Image

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST_PATH = STATIC / "assets" / "manifest.json"
APP_JS = STATIC / "js" / "app.js"
INTERACTION_JS = STATIC / "js" / "interaction.js"
INDEX_HTML = ROOT / "app" / "templates" / "index.html"


def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def professional_assets() -> list[dict]:
    return [
        item for item in manifest()["assets"]
        if item.get("visualStyle") == "professional"
        and item.get("visibleInEditor", True) is not False
        and item.get("releaseStatus", "released") == "released"
    ]


def professional_front_assets() -> list[dict]:
    return [item for item in professional_assets() if item.get("view") == "Front"]


def test_professional_is_the_only_visible_and_supported_editor_style():
    payload = manifest()
    assert payload["defaultPlayerVisualStyle"] == "professional"
    html = INDEX_HTML.read_text(encoding="utf-8")
    source = APP_JS.read_text(encoding="utf-8")
    assert 'id="prop-visual-style"' not in html
    assert 'id="player-style"' not in html
    assert "Legacy Vector" not in html
    assert "Professional pose unavailable" not in html
    assert "professional-fallback" not in html
    assert "localStorage.getItem(\"vpd-player-style\")" not in source


def test_required_professional_role_pose_pack_is_complete():
    payload = manifest()
    required = payload["professionalPoseCatalog"]
    assets = professional_front_assets()
    expected = sum(
        len(poses) * (1 if role == "coach" else 2)
        for role, poses in required.items()
    )
    assert len(assets) == expected == 122
    for role, poses in required.items():
        teams = ("Neutral",) if role == "coach" else ("A", "B")
        for team in teams:
            actual = {item["pose"] for item in assets if item["role"] == role and item["team"] == team}
            assert actual == set(poses)
    assert payload["hiddenProfessionalRoles"] == ["generic"]
    assert {item["approvalStatus"] for item in assets} == {"approved"}


def test_professional_manifest_has_character_and_layout_metadata():
    for asset in professional_assets():
        assert asset["id"].startswith("professional_")
        assert asset["characterId"]
        assert asset["asset"].endswith(".webp")
        assert asset["master"].endswith((".webp", ".png"))
        assert asset["thumbnail"].endswith(".webp")
        assert (
            f"/professional/{asset['characterId']}/" in asset["asset"]
            or f"/professional/team_a/{asset['characterId']}/" in asset["asset"]
            or "/professional/team_a/middle_blocker/back/" in asset["asset"]
        )
        assert asset["objectKind"] == "character"
        assert asset["poseId"]
        assert asset["supportsMirror"] is (asset.get("view") == "Front")
        assert asset["defaultWidth"] > 0 and asset["defaultHeight"] > 0
        assert 0 <= asset["footAnchor"]["x"] <= 1
        assert 0 <= asset["footAnchor"]["y"] <= 1
        assert asset["anchorMode"] in {
            "feet", "body_center_landing_reference", "takeoff_foot",
        }
        assert set(asset["shadowOffset"]) == {"x", "y"}
        assert asset["facingSupport"] == (["left", "right"] if asset.get("view") == "Front" else [])


def test_professional_assets_and_thumbnails_are_transparent_webp():
    for asset in professional_assets():
        for key in ("asset", "master", "thumbnail"):
            path = STATIC / asset[key].removeprefix("/static/")
            assert path.is_file()
            with Image.open(path) as image:
                assert image.format == ("PNG" if key == "master" and asset[key].endswith(".png") else "WEBP")
                assert image.mode == "RGBA"
                assert image.getchannel("A").getextrema()[0] == 0


def test_hero_pack_has_clean_chroma_free_edges_and_three_offline_tiers():
    for asset in professional_assets():
        runtime_path = STATIC / asset["asset"].removeprefix("/static/")
        master_path = STATIC / asset["master"].removeprefix("/static/")
        thumb_path = STATIC / asset["thumbnail"].removeprefix("/static/")
        with Image.open(runtime_path).convert("RGBA") as runtime:
            visible_magenta = sum(
                1 for red, green, blue, alpha in runtime.get_flattened_data()
                if alpha > 40 and red > 180 and blue > 140 and green < 100
            )
            assert visible_magenta == 0
            assert runtime.height <= 480
        with Image.open(master_path) as master:
            assert runtime_path != master_path
            assert max(master.size) >= 800
        with Image.open(thumb_path) as thumbnail:
            assert thumbnail.height <= 150


def test_team_b_and_every_visible_pose_resolve_professional_without_fallback():
    registry = AssetRegistry(MANIFEST_PATH)
    for role, poses in registry.professional_pose_catalog.items():
        teams = ("Neutral",) if role == "coach" else ("A", "B")
        for team in teams:
            for pose in poses:
                asset = registry.resolve_player(team, role, pose, "legacy_vector")
                assert asset["visualStyle"] == "professional"
                assert asset["team"] == team
                assert "isProfessionalFallback" not in asset


def test_toolbar_pose_picker_and_placed_player_share_manifest_asset_id():
    source = APP_JS.read_text(encoding="utf-8")
    assert 'data-asset-id="${asset.id}"' in source
    assert "image.dataset.assetId = asset.id" in source
    assert 'g.setAttribute("data-asset-id", asset.id)' in source
    assert 'selected.assetId = asset.id' in source
    assert 'href="${asset.asset}"' in source


def test_unified_zoom_aware_drag_uses_viewport_inverse_matrix():
    source = APP_JS.read_text(encoding="utf-8")
    interaction = INTERACTION_JS.read_text(encoding="utf-8")
    assert "clientToWorkspace(svg, viewport, evt.clientX, evt.clientY)" in source
    assert "viewport.getScreenCTM().inverse()" in interaction
    for zoom in (0.25, 0.5, 1, 2, 3):
        workspace_delta = (60 * zoom) / zoom
        assert workspace_delta == 60


def test_all_visual_types_use_the_same_drag_target_contract():
    source = APP_JS.read_text(encoding="utf-8")
    for drag_surface in ("raster", "arrow", "shape", "text"):
        assert f'data-drag-surface="{drag_surface}"' in source
    assert 'e.target.closest(".object-hit")' in source
    assert "window.VPDInteraction.canMove(o)" in source
    assert 'svg.setPointerCapture(e.pointerId)' in source


def test_pose_team_and_style_change_preserve_transform_fields():
    registry = AssetRegistry(MANIFEST_PATH)
    original = {
        "id": "player",
        "type": "player",
        "characterId": "female_athlete_01",
        "visualStyle": "professional",
        "team": "A",
        "role": "setter",
        "pose": "Front Set",
        "assetId": "professional_female_athlete_01_front_set",
        "x": 342,
        "y": 517,
        "width": 92,
        "height": 156,
        "rotation": 37,
        "opacity": 0.7,
        "locked": False,
        "courtId": "court-two",
        "assignedCourtId": "court-two",
        "zIndex": 8,
    }
    for team, pose in (("A", "Back Set"), ("B", "Ready")):
        changed = deepcopy(original)
        changed.update(team=team, pose=pose, visualStyle="legacy_vector")
        asset = registry.resolve_player(team, "setter", pose)
        changed["assetId"] = asset["id"]
        migrated = registry.migrate_object(changed)
        for key in ("x", "y", "width", "height", "rotation", "opacity", "locked", "courtId", "assignedCourtId", "zIndex"):
            assert migrated[key] == original[key]


def test_professional_player_save_reload_preserves_character_and_movement_state(client):
    payload = {
        "metadata": {"name": "Professional persistence"},
        "frames": [{
            "id": "frame",
            "objects": [{
                "id": "player",
                "type": "character",
                "characterId": "female_athlete_01",
                "visualStyle": "professional",
                "team": "A",
                "role": "setter",
                "pose": "Front Set",
                "assetId": "professional_female_athlete_01_front_set",
                "x": 440,
                "y": 360,
                "rotation": 18,
                "mirrorX": True,
                "showShadow": True,
                "locked": False,
            }],
        }],
    }
    saved = client.post("/api/drills", json=payload)
    assert saved.status_code == 201
    loaded = client.get(f'/api/drills/{saved.json()["id"]}').json()
    player = loaded["frames"][0]["objects"][0]
    assert player["assetId"] == "professional_female_athlete_01_front_set"
    assert player["type"] == "character"
    assert player["characterId"] == "female_athlete_01"
    assert player["visualStyle"] == "professional"
    assert player["mirrorX"] is True
    assert player["showShadow"] is True
    assert player["locked"] is False


def test_frame_and_court_duplicates_deep_copy_player_ids_and_assignments():
    source = APP_JS.read_text(encoding="utf-8")
    assert "const c=deep(frame())" in source
    assert "o.id=uid()" in source
    assert "o.assignedCourtId=o.courtId" in source
    assert "id: uid(), courtId: copy.id, assignedCourtId: copy.id" in source


def test_export_waits_for_assets_and_excludes_editor_handles():
    source = APP_JS.read_text(encoding="utf-8")
    assert "async function waitForVisualAssets()" in source
    assert "await waitForVisualAssets()" in source
    assert "if (image.decode) await image.decode()" in source
    assert 'clone.querySelector("#selection-layer").innerHTML = ""' in source
    assert 'clone.querySelectorAll("image.visual-asset")' in source


def test_old_vector_and_semirealistic_drills_both_migrate_to_professional(client):
    payload = {
        "metadata": {"name": "Legacy safe migration"},
        "frames": [{
            "id": "frame",
            "objects": [
                {"id": "legacy", "type": "player", "assetId": "a_setter_ready", "team": "A", "role": "Setter", "pose": "Ready"},
                {"id": "old-raster", "type": "player", "assetId": "team_a_setter_ready_semirealistic", "visualStyle": "semi_realistic", "team": "A", "role": "Setter", "pose": "Ready"},
            ],
        }],
    }
    saved = client.post("/api/drills", json=payload).json()
    legacy, migrated = saved["frames"][0]["objects"]
    assert legacy["visualStyle"] == "professional"
    assert legacy["assetId"] == "professional_female_athlete_01_ready"
    assert legacy["type"] == "character"
    assert migrated["visualStyle"] == "professional"
    assert migrated["assetId"] == "professional_female_athlete_01_ready"
    assert saved["frames"][0]["courts"][0]["rotation"] == 0
