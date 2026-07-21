from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
INDEX = ROOT / "app" / "templates" / "index.html"
APP_JS = STATIC / "js" / "app.js"


def registry() -> AssetRegistry:
    return AssetRegistry(MANIFEST)


def test_player_style_selector_legacy_option_and_warning_are_absent():
    html = INDEX.read_text(encoding="utf-8")
    assert "prop-visual-style" not in html
    assert 'id="player-style"' not in html
    assert "Legacy Vector" not in html
    assert "Professional pose unavailable" not in html


def test_outside_and_middle_visible_pose_catalogs_are_complete():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert {
        "Attack Start", "Approach Step 1", "Approach Step 2", "Takeoff",
        "Jump Attack", "High Contact", "Line Attack", "Cross-Court Attack",
        "Tip", "Roll Shot", "Back-Row Attack", "Landing",
        "Transition After Attack",
    }.issubset(payload["professionalPoseCatalog"]["outside"])
    assert {
        "Quick Attack Ready", "First-Tempo Approach", "Takeoff",
        "Front Quick Attack", "Behind Setter Quick", "One-Foot Slide Approach",
        "One-Foot Slide Takeoff", "Slide Attack Contact", "Gap Attack",
        "Push Attack", "Landing", "Transition After Attack",
    }.issubset(payload["professionalPoseCatalog"]["middle"])


def test_every_visible_role_pose_team_has_one_existing_professional_asset():
    loaded = registry()
    for role, poses in loaded.professional_pose_catalog.items():
        teams = ("Neutral",) if role == "coach" else ("A", "B")
        for team in teams:
            for pose in poses:
                asset = loaded.resolve_player(team, role, pose)
                assert asset["visualStyle"] == "professional"
                assert asset["team"] == team
                assert (STATIC / asset["asset"].removeprefix("/static/")).is_file()
                assert (STATIC / asset["thumbnail"].removeprefix("/static/")).is_file()


def test_required_outside_and_middle_actions_resolve_professional():
    loaded = registry()
    for team in ("A", "B"):
        for role, pose in (
            ("Outside", "Reception"),
            ("Outside", "Jump Attack"),
            ("Middle", "Block"),
            ("Middle", "Quick Attack"),
        ):
            assert loaded.resolve_player(team, role, pose)["visualStyle"] == "professional"


def test_style_parameter_cannot_force_a_legacy_editor_asset():
    loaded = registry()
    asset = loaded.resolve_player("A", "Outside", "Reception", "legacy_vector")
    assert asset["visualStyle"] == "professional"
    assert asset["id"] == "professional_female_athlete_02_reception"


def test_legacy_migration_preserves_all_transform_and_membership_fields():
    loaded = registry()
    old = {
        "id": "legacy-outside",
        "type": "player",
        "assetId": "b_outside_standing",
        "visualStyle": "legacy_vector",
        "team": "B",
        "role": "Outside",
        "pose": "Standing",
        "x": 411,
        "y": 522,
        "width": 81,
        "height": 149,
        "rotation": 47,
        "mirrorX": True,
        "locked": True,
        "zIndex": 9,
        "courtId": "court-two",
        "assignedCourtId": "court-two",
    }
    migrated = loaded.migrate_object(deepcopy(old))
    assert migrated["type"] == "character"
    assert migrated["visualStyle"] == "professional"
    assert migrated["pose"] == "Ready"
    assert migrated["assetId"] == "professional_team_b_female_athlete_02_ready"
    for field in (
        "x", "y", "width", "height", "rotation", "mirrorX", "locked",
        "zIndex", "courtId", "assignedCourtId",
    ):
        assert migrated[field] == old[field]


def test_team_and_pose_changes_cannot_change_visual_style():
    source = APP_JS.read_text(encoding="utf-8")
    assert 'if (["team", "role", "pose"].includes(key) && isCharacter(o))' in source
    assert 'o.visualStyle = "professional"' in source
    assert 'exact("legacy_vector")' not in source
    assert 'return exact("legacy_vector")' not in source


def test_save_reload_preserves_professional_asset_id_and_transforms(client):
    payload = {
        "metadata": {"name": "Professional-only persistence"},
        "frames": [{
            "id": "frame",
            "objects": [{
                "id": "middle",
                "type": "character",
                "visualStyle": "professional",
                "team": "B",
                "role": "Middle",
                "pose": "Quick Attack",
                "assetId": "professional_team_b_female_athlete_03_quick_attack",
                "x": 301,
                "y": 402,
                "rotation": 25,
                "mirrorX": True,
                "locked": True,
            }],
        }],
    }
    saved = client.post("/api/drills", json=payload)
    assert saved.status_code == 201
    loaded = client.get(f'/api/drills/{saved.json()["id"]}').json()
    player = loaded["frames"][0]["objects"][0]
    assert player["assetId"] == "professional_team_b_female_athlete_03_quick_attack"
    assert player["visualStyle"] == "professional"
    assert player["rotation"] == 25
    assert player["mirrorX"] is True
    assert player["locked"] is True


def test_export_uses_rendered_professional_assets_and_excludes_editor_ui():
    source = APP_JS.read_text(encoding="utf-8")
    assert 'clone.querySelectorAll("image.visual-asset")' in source
    assert 'clone.querySelector("#selection-layer").innerHTML = ""' in source
    assert 'if (asset.category === "fallback" || asset.visualStyle === "legacy_vector") return false;' in source
