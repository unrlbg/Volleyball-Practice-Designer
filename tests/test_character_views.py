from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
APP_JS = STATIC / "js" / "app.js"
INDEX_HTML = ROOT / "app" / "templates" / "index.html"

CHARACTER_VIEWS = ["Front", "3/4 Front Left", "3/4 Front Right", "Left Side", "Right Side", "3/4 Back Left", "3/4 Back Right", "Back", "45° Back"]
BACKSIDE_VIEWS = ["Back", "3/4 Back Left", "3/4 Back Right", "45° Back"]
RELEASED_BACKSIDE_IDS = {
    "professional_team_a_middle_standing_on_net_prepared_to_jump_back",
    "professional_team_a_middle_standing_on_net_block_ready_back",
    "professional_team_a_middle_jump_block_back",
    "professional_team_a_middle_jump_block_left_back",
    "professional_team_a_middle_jump_block_right_back",
    "professional_team_a_middle_jump_block_spread_back",
    "professional_team_a_middle_jump_block_close_back",
    "professional_team_a_middle_quick_block_back",
    "professional_female_athlete_01_ready_back",
    "professional_team_b_female_athlete_01_ready_back",
    "professional_female_athlete_01_front_set_back",
    "professional_team_b_female_athlete_01_front_set_back",
    "professional_female_athlete_01_back_set_back",
    "professional_team_b_female_athlete_01_back_set_back",
    "professional_female_athlete_01_jump_set_back",
    "professional_team_b_female_athlete_01_jump_set_back",
    "professional_female_athlete_01_one_hand_set_back",
    "professional_team_b_female_athlete_01_one_hand_set_back",
    "professional_female_athlete_01_setter_dump_back",
    "professional_team_b_female_athlete_01_setter_dump_back",
    "professional_female_athlete_01_transition_back",
    "professional_team_b_female_athlete_01_transition_back",
    "professional_female_athlete_01_defensive_ready_back",
    "professional_team_b_female_athlete_01_defensive_ready_back",
    "professional_female_athlete_01_emergency_set_back",
    "professional_team_b_female_athlete_01_emergency_set_back",
}


def is_released_backside_id(asset_id: str) -> bool:
    return asset_id in RELEASED_BACKSIDE_IDS


def pptx_slide_count(path: Path) -> int:
    with ZipFile(path) as pptx:
        return sum(1 for name in pptx.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))


def test_asset_api_advertises_exact_professional_character_views(client):
    payload = client.get("/api/assets").json()

    assert payload["defaultCharacterView"] == "Front"
    assert payload["professionalCharacterViews"] == CHARACTER_VIEWS


def test_only_released_professional_backside_assets_are_visible():
    registry = AssetRegistry(MANIFEST)
    backside = [
        asset for asset in registry.assets
        if asset.get("category") == "player"
        and asset.get("visualStyle") == "professional"
        and asset.get("view") != "Front"
    ]

    assert all(is_released_backside_id(asset["id"]) for asset in backside)
    assert not [asset for asset in backside if asset["id"].startswith("professional_45_back_")]
    assert {asset["view"] for asset in backside} == {"Back"}
    assert all(asset.get("professionalGrade") is True for asset in backside)
    assert all(asset.get("releaseStatus") == "released" for asset in backside)


def test_hidden_unfinished_assets_are_not_returned_by_api(client):
    payload = client.get("/api/assets").json()
    professional = [
        asset for asset in payload["assets"]
        if asset.get("category") == "player"
        and asset.get("visualStyle") == "professional"
    ]

    assert all(asset.get("visibleInEditor", True) is not False for asset in professional)
    assert all(asset.get("releaseStatus", "released") == "released" for asset in professional)
    assert all(asset.get("professionalGrade", True) is not False for asset in professional)
    assert all(
        is_released_backside_id(asset["id"])
        for asset in professional
        if asset.get("view") != "Front"
    )


def test_unreleased_backside_view_returns_controlled_error():
    registry = AssetRegistry(MANIFEST)

    with pytest.raises(ValueError, match="No Professional Back asset"):
        registry.resolve_player("A", "outside", "Jump Attack", character_view="Back")


def test_missing_front_side_views_are_not_exposed():
    registry = AssetRegistry(MANIFEST)
    outside_jump = [
        asset for asset in registry.assets
        if asset.get("role") == "outside"
        and asset.get("team") == "A"
        and asset.get("pose") == "Jump Attack"
        and asset.get("visualStyle") == "professional"
    ]
    views = {asset["view"] for asset in outside_jump}

    assert views == {"Front"}
    assert "Left Side" not in views
    assert "Right Side" not in views
    assert "3/4 Front Left" not in views
    assert "3/4 Front Right" not in views


def test_no_unreleased_backside_option_maps_to_mirrored_front_or_legacy_vector():
    registry = AssetRegistry(MANIFEST)

    for view in BACKSIDE_VIEWS:
        with pytest.raises(ValueError, match="No Professional"):
            registry.resolve_player("A", "libero", "Reception", character_view=view)


def test_character_view_migration_preserves_drill_object_state():
    registry = AssetRegistry(MANIFEST)
    original = {
        "id": "player",
        "type": "character",
        "characterId": "female_athlete_01",
        "visualStyle": "professional",
        "team": "B",
        "role": "setter",
        "pose": "Front Set",
        "characterView": "Back",
        "assetId": "professional_team_b_female_athlete_01_front_set",
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
        "layer": 8,
        "showShadow": False,
    }

    migrated = registry.migrate_object(original)

    assert migrated["characterView"] == "Back"
    assert migrated["assetId"] == "professional_team_b_female_athlete_01_front_set_back"
    assert migrated["characterId"] == "female_athlete_01"
    assert migrated["role"] == "setter"
    assert migrated["pose"] == "Front Set"
    assert migrated["team"] == "B"
    for key in ("x", "y", "width", "height", "rotation", "opacity", "locked", "courtId", "assignedCourtId", "zIndex", "showShadow"):
        assert migrated[key] == original[key]


def test_released_setter_back_character_view_persists_through_save_reload(client):
    payload = {
        "metadata": {"name": "Back view drill"},
        "frames": [{
            "id": "frame-one",
            "objects": [{
                "id": "player",
                "type": "character",
                "team": "A",
                "role": "setter",
                "pose": "Front Set",
                "characterView": "Back",
                "assetId": "professional_female_athlete_01_front_set",
                "x": 440,
                "y": 360,
                "rotation": 18,
                "mirrorX": False,
                "showShadow": True,
            }],
        }],
    }

    saved = client.post("/api/drills", json=payload)
    assert saved.status_code == 201
    loaded = client.get(f'/api/drills/{saved.json()["id"]}').json()
    player = loaded["frames"][0]["objects"][0]

    assert player["characterView"] == "Back"
    assert player["assetId"] == "professional_female_athlete_01_front_set_back"
    assert player["mirrorX"] is False
    assert player["rotation"] == 18


def test_frame_duplication_preserves_character_view():
    source = APP_JS.read_text(encoding="utf-8")

    assert "const c=deep(frame())" in source
    assert "c.objects.forEach(o=>{o.id=uid()" in source
    assert "delete o.characterView" not in source


def test_pptx_player_export_uses_selected_backside_view(client):
    registry = AssetRegistry(MANIFEST)
    back = registry.resolve_player("A", "middle", "Jump Block", character_view="Back")

    response = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "pptx", "assetIds": [back["id"]]})
    assert response.status_code == 200
    deck = Path(response.json()["decks"][0]["path"])

    assert deck.is_file()
    assert pptx_slide_count(deck) == 1


def test_png_pack_includes_backside_assets(client):
    registry = AssetRegistry(MANIFEST)
    back = registry.resolve_player("A", "middle", "Quick Block", character_view="Back")

    response = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "png", "assetIds": [back["id"]]})
    assert response.status_code == 200
    paths = [Path(path) for path in response.json()["pngPaths"]]

    assert len(paths) == 1
    assert paths[0].is_file()
    assert "quick_block_back" in paths[0].name


def test_editor_exposes_character_view_thumbnails_without_using_mirroring():
    html = INDEX_HTML.read_text(encoding="utf-8")
    source = APP_JS.read_text(encoding="utf-8")

    assert 'id="prop-character-view"' in html
    assert 'id="character-view-picker"' in html
    assert 'data-character-view="${escapeHtml(view)}"' in source
    assert "characterViewAssets(o.team, o.role, o.pose)" in source
    assert '["prop-character-view","characterView"]' in source
    assert 'if (key === "facing")' in source
    assert 'o.mirrorX = value === "Left"' in source
