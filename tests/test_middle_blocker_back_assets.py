from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest
from PIL import Image

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
APP_JS = STATIC / "js" / "app.js"
INDEX_HTML = ROOT / "app" / "templates" / "index.html"

MIDDLE_BACK_POSES = [
    "Standing on Net - Prepared to Jump",
    "Standing on Net - Block Ready",
    "Jump Block",
    "Jump Block Left",
    "Jump Block Right",
    "Jump Block Spread",
    "Jump Block Close",
    "Quick Block",
]


def slide_count(path: Path) -> int:
    with ZipFile(path) as deck:
        return sum(1 for name in deck.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))


@pytest.fixture(scope="module")
def registry() -> AssetRegistry:
    return AssetRegistry(MANIFEST)


def local(path: str) -> Path:
    return STATIC / path.removeprefix("/static/")


def test_every_exposed_middle_back_pose_has_valid_professional_asset(registry):
    for pose in MIDDLE_BACK_POSES:
        asset = registry.resolve_player("A", "middle", pose, character_view="Back")
        assert asset["role"] == "middle"
        assert asset["team"] == "A"
        assert asset["view"] == "Back"
        assert asset["visualStyle"] == "professional"
        assert asset["characterId"] == "female_athlete_03"
        assert asset["containsNet"] is False
        assert asset["containsCourt"] is False
        assert asset["supportsMirror"] is False
        assert asset["facingSupport"] == []
        for field in ("master", "asset", "thumbnail"):
            assert local(asset[field]).is_file()


def test_only_quality_released_middle_back_poses_are_exposed(registry):
    visible_back_poses = {
        asset["pose"] for asset in registry.assets
        if asset.get("category") == "player"
        and asset.get("visualStyle") == "professional"
        and asset.get("team") == "A"
        and asset.get("role") == "middle"
        and asset.get("view") == "Back"
    }

    assert visible_back_poses == set(MIDDLE_BACK_POSES)
    assert len(visible_back_poses) == 8


@pytest.mark.parametrize("pose", ["Block Ready", "Single Block", "Moving Block", "Quick Attack", "Roll Shot"])
def test_unfinished_middle_back_poses_are_hidden(registry, pose):
    with pytest.raises(ValueError, match="No Professional"):
        registry.resolve_player("A", "middle", pose, character_view="Back")


@pytest.mark.parametrize("pose", MIDDLE_BACK_POSES)
def test_priority_jump_block_back_assets_exist_and_are_transparent(registry, pose):
    asset = registry.resolve_player("A", "middle", pose, character_view="Back")

    with Image.open(local(asset["master"])) as master, Image.open(local(asset["asset"])) as runtime:
        assert master.format == "PNG"
        assert master.mode == "RGBA"
        assert max(master.size) >= 1024
        assert runtime.format == "WEBP"
        assert runtime.mode == "RGBA"
        assert 400 <= runtime.height <= 600
        assert runtime.getchannel("A").getextrema()[0] == 0


def test_back_asset_is_different_from_existing_front_asset(registry):
    front = registry.resolve_player("A", "middle", "Ready", character_view="Front")
    back = registry.resolve_player("A", "middle", "Jump Block", character_view="Back")

    assert back["id"] != front["id"]
    assert back["asset"] != front["asset"]
    assert local(back["asset"]).read_bytes() != local(front["asset"]).read_bytes()


def test_back_only_poses_do_not_resolve_to_front_or_side_views(registry):
    jump_back = registry.resolve_player("A", "middle", "Jump Block", character_view="Back")

    assert jump_back["id"] == "professional_team_a_middle_jump_block_back"
    with pytest.raises(ValueError):
        registry.resolve_player("A", "middle", "Jump Block", character_view="Front")
    with pytest.raises(ValueError):
        registry.resolve_player("A", "middle", "Jump Block", character_view="Left Side")


def test_middle_back_change_preserves_transform_and_state(registry):
    original = {
        "id": "middle",
        "type": "character",
        "team": "A",
        "role": "middle",
        "pose": "Jump Block",
        "characterView": "Back",
        "assetId": "professional_female_athlete_03_block_ready",
        "x": 610,
        "y": 420,
        "width": 110,
        "height": 210,
        "rotation": 12,
        "opacity": 0.82,
        "locked": True,
        "courtId": "court-a",
        "assignedCourtId": "court-a",
        "zIndex": 9,
        "showShadow": False,
    }

    migrated = registry.migrate_object(original)

    assert migrated["assetId"] == "professional_team_a_middle_jump_block_back"
    assert migrated["characterView"] == "Back"
    for key in ("x", "y", "width", "height", "rotation", "opacity", "locked", "courtId", "assignedCourtId", "zIndex", "showShadow"):
        assert migrated[key] == original[key]


def test_save_reload_preserves_middle_back_view(client):
    payload = {
        "metadata": {"name": "Middle back block"},
        "frames": [{
            "id": "frame-one",
            "objects": [{
                "id": "middle",
                "type": "character",
                "team": "A",
                "role": "middle",
                "pose": "Jump Block",
                "characterView": "Back",
                "assetId": "professional_team_a_middle_jump_block_back",
                "x": 610,
                "y": 420,
            }],
        }],
    }

    saved = client.post("/api/drills", json=payload)
    assert saved.status_code == 201
    loaded = client.get(f'/api/drills/{saved.json()["id"]}').json()
    player = loaded["frames"][0]["objects"][0]

    assert player["pose"] == "Jump Block"
    assert player["characterView"] == "Back"
    assert player["assetId"] == "professional_team_a_middle_jump_block_back"


def test_frame_and_court_duplication_preserve_middle_back_view_source():
    source = APP_JS.read_text(encoding="utf-8")

    assert "const c=deep(frame())" in source
    assert "duplicateCourt(withContents" in source
    assert "delete o.characterView" not in source
    assert "delete item.characterView" not in source


def test_powerpoint_and_png_export_use_middle_back_asset(client, registry):
    asset = registry.resolve_player("A", "middle", "Jump Block", character_view="Back")

    pptx = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "pptx", "assetIds": [asset["id"]]})
    assert pptx.status_code == 200
    deck = Path(pptx.json()["decks"][0]["path"])
    assert deck.is_file()
    assert slide_count(deck) == 1

    png = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "png", "assetIds": [asset["id"]]})
    assert png.status_code == 200
    exported = Path(png.json()["pngPaths"][0])
    assert exported.is_file()
    assert "jump_block_back" in exported.name


def test_asset_library_has_role_and_view_filters_for_middle_back():
    html = INDEX_HTML.read_text(encoding="utf-8")
    source = APP_JS.read_text(encoding="utf-8")

    assert 'id="asset-role"' in html
    assert 'id="asset-view"' in html
    assert '<option value="middle">Middle Blocker</option>' in html
    assert '<option value="Back">Back</option>' in html
    assert 'const role = $("#asset-role")?.value || "";' in source
    assert 'const view = $("#asset-view")?.value || "";' in source
