from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
VIEW = "45° Back"
REQUIRED_SETTER_45_BACK_POSES = [
    "Defense Ready",
    "Defensive Shuffle",
    "Split Step",
    "Low Defensive Position",
    "Left Defensive Position",
    "Right Defensive Position",
    "Deep Defense",
    "Mid Defense",
    "Short Defense",
    "Line Defense",
    "Cross-Court Defense",
    "Cover Behind Block",
    "Pipe Defense",
    "Transition Defense",
    "Forearm Dig",
    "One Knee Dig",
    "Side Lunge Dig",
    "Split Dig",
    "Emergency Dig",
    "Forward Dive",
    "Side Dive",
    "Pancake",
    "Sprawl Defense",
    "Roll Recovery",
]
HIDDEN_SETTER_45_BACK_POSES = {"Get Up", "Transition", "Ready Again"}
DEFENSIVE_GROUPS = {
    "General Defense",
    "Court Coverage",
    "Digging",
    "Diving",
    "After Defense",
}


def setter_45_back_assets(registry: AssetRegistry) -> list[dict]:
    return [
        asset for asset in registry.library_assets
        if asset.get("characterId") == "female_athlete_01"
        and asset.get("team") == "A"
        and asset.get("role") == "setter"
        and asset.get("view") == VIEW
    ]


def test_approved_45_back_defensive_assets_are_released():
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    generated = [
        asset for asset in raw["assets"]
        if asset.get("id", "").startswith("professional_45_back_")
    ]
    registry = AssetRegistry(MANIFEST)
    visible_generated = [asset for asset in generated if asset.get("visibleInEditor") is True]

    assert len(generated) == 162
    assert len(visible_generated) == 144
    assert all(asset["releaseStatus"] == "released" for asset in visible_generated)
    assert all(asset["releaseState"] == "released" for asset in visible_generated)
    assert all(asset["isReleased"] is True for asset in visible_generated)
    assert all(asset["isApproved"] is True for asset in visible_generated)
    assert len([
        asset for asset in registry.assets
        if asset.get("id", "").startswith("professional_45_back_")
    ]) == 144
    assert len([
        asset for asset in registry.library_assets
        if asset.get("id", "").startswith("professional_45_back_")
    ]) == 144


def test_all_released_45_back_roles_have_only_required_professional_defensive_poses():
    registry = AssetRegistry(MANIFEST)
    assets = [
        asset for asset in registry.library_assets
        if asset.get("id", "").startswith("professional_45_back_")
    ]
    groups = {}

    for asset in assets:
        groups.setdefault(
            (asset["team"], asset["role"], asset["characterId"]),
            [],
        ).append(asset)

    assert set(groups) == {
        ("A", "setter", "female_athlete_01"),
        ("A", "outside", "female_athlete_02"),
        ("A", "opposite", "female_athlete_05"),
        ("A", "middle", "female_athlete_03"),
        ("A", "libero", "female_athlete_04"),
        ("Neutral", "coach", "coach_01"),
    }
    for role_assets in groups.values():
        assert [asset["pose"] for asset in role_assets] == REQUIRED_SETTER_45_BACK_POSES
        assert all(asset["releaseStatus"] == "released" for asset in role_assets)
        assert all(asset["visibleInEditor"] is True for asset in role_assets)
        assert all(asset.get("professionalGrade") is True for asset in role_assets)


def test_team_a_setter_45_back_professional_pack_has_exact_required_poses():
    registry = AssetRegistry(MANIFEST)
    assets = setter_45_back_assets(registry)

    assert [asset["pose"] for asset in assets] == REQUIRED_SETTER_45_BACK_POSES
    assert len(assets) == 24
    assert len({asset["id"] for asset in assets}) == 24
    assert len({
        (asset["team"], asset["role"], asset["pose"], asset["view"])
        for asset in assets
    }) == 24
    assert all(asset["visualStyle"] == "professional" for asset in assets)
    assert all(asset["releaseStatus"] == "released" for asset in assets)
    assert all(asset["visibleInEditor"] is True for asset in assets)
    assert all(asset.get("professionalGrade") is True for asset in assets)
    assert all(asset.get("supportsMirror") is False for asset in assets)
    assert all(asset.get("showShadow") is True for asset in assets)


def test_team_a_setter_45_back_assets_have_runtime_master_and_thumbnail_files():
    registry = AssetRegistry(MANIFEST)

    for asset in setter_45_back_assets(registry):
        runtime = STATIC / asset["asset"].removeprefix("/static/")
        thumbnail = STATIC / asset["thumbnail"].removeprefix("/static/")
        master = STATIC / asset["sourceMaster"].removeprefix("/static/")
        assert runtime.is_file(), asset["id"]
        assert thumbnail.is_file(), asset["id"]
        assert master.is_file(), asset["id"]
        with Image.open(master) as image:
            assert image.mode == "RGBA"
            assert max(image.size) >= 1024
        with Image.open(runtime) as image:
            assert image.mode == "RGBA"
            assert max(image.size) >= 400
            assert image.height <= 480
        with Image.open(thumbnail) as image:
            assert image.mode == "RGBA"
            assert image.height <= 150
            assert max(image.size) >= 100


def test_old_extra_setter_45_back_poses_are_hidden_from_normal_library():
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    registry = AssetRegistry(MANIFEST)
    visible_ids = {asset["id"] for asset in registry.library_assets}
    extras = [
        asset for asset in raw["assets"]
        if asset.get("characterId") == "female_athlete_01"
        and asset.get("team") == "A"
        and asset.get("role") == "setter"
        and asset.get("view") == VIEW
        and asset.get("pose") in HIDDEN_SETTER_45_BACK_POSES
    ]

    assert {asset["pose"] for asset in extras} == HIDDEN_SETTER_45_BACK_POSES
    assert all(asset["visibleInEditor"] is False for asset in extras)
    assert all(str(asset["releaseStatus"]).startswith("hidden") for asset in extras)
    assert visible_ids.isdisjoint({asset["id"] for asset in extras})


def test_asset_library_filters_return_team_a_setter_45_back_pack(client):
    payload = client.get("/api/assets").json()
    filtered = [
        asset for asset in payload["libraryAssets"]
        if asset.get("category") == "player"
        and asset.get("visualStyle") == "professional"
        and asset.get("team") == "A"
        and asset.get("role") == "setter"
        and asset.get("view") == VIEW
    ]

    assert [asset["pose"] for asset in filtered] == REQUIRED_SETTER_45_BACK_POSES


def test_setter_45_back_save_reload_and_frame_duplicate_preserve_asset(client):
    registry = AssetRegistry(MANIFEST)
    asset = next(item for item in setter_45_back_assets(registry) if item["pose"] == "Forearm Dig")
    payload = {
        "metadata": {"name": "Setter 45 back validation"},
        "frames": [{
            "id": "frame-one",
            "objects": [{
                "id": "setter-dig",
                "type": "character",
                "assetId": asset["id"],
                "characterId": asset["characterId"],
                "team": "A",
                "role": "setter",
                "pose": "Forearm Dig",
                "characterView": VIEW,
                "x": 420,
                "y": 340,
                "width": asset["defaultWidth"],
                "height": asset["defaultHeight"],
                "rotation": 18,
                "opacity": 0.85,
                "locked": True,
                "showShadow": True,
            }],
        }],
    }

    saved = client.post("/api/drills", json=payload)
    assert saved.status_code == 201
    drill = saved.json()
    duplicate = client.post(f"/api/drills/{drill['id']}/duplicate")
    assert duplicate.status_code == 201
    loaded = client.get(f"/api/drills/{drill['id']}").json()
    player = loaded["frames"][0]["objects"][0]

    assert player["assetId"] == asset["id"]
    assert player["characterId"] == "female_athlete_01"
    assert player["characterView"] == VIEW
    for key in ("x", "y", "width", "height", "rotation", "opacity", "locked", "showShadow"):
        assert player[key] == payload["frames"][0]["objects"][0][key]


def test_setter_45_back_exports_use_professional_runtime_assets(client):
    registry = AssetRegistry(MANIFEST)
    asset = next(item for item in setter_45_back_assets(registry) if item["pose"] == "Pancake")

    pptx = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "pptx", "assetIds": [asset["id"]]})
    png = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "png", "assetIds": [asset["id"]]})

    assert pptx.status_code == 200
    assert png.status_code == 200
    assert Path(pptx.json()["decks"][0]["path"]).is_file()
    png_paths = [Path(path) for path in png.json()["pngPaths"]]
    assert len(png_paths) == 1
    assert png_paths[0].is_file()
    assert "pancake" in png_paths[0].name


def test_defensive_pose_groups_remain_catalog_controlled_until_editor_palette_release():
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for role, groups in raw["professionalPoseGroups"].items():
        assert DEFENSIVE_GROUPS.isdisjoint(groups), role
    for role, poses in raw["professionalPoseCatalog"].items():
        assert "Defense Ready" not in poses, role
        assert "Forearm Dig" not in poses, role
        assert "Pancake" not in poses, role


def test_asset_library_cards_can_place_exact_released_asset_in_editor():
    source = (ROOT / "app" / "static" / "js" / "app.js").read_text(encoding="utf-8")

    assert "function addAssetLibraryObject(asset)" in source
    assert 'button.dataset.assetPlace = assetId' in source
    assert 'addAssetLibraryObject(assetIndex.get(assetId))' in source
    assert 'showView("editor")' in source
    assert 'assetId: asset.id' in source
    assert 'characterView: normalizeCharacterView(asset.view || asset.characterView)' in source


def test_45_back_defensive_resolution_uses_released_assets():
    registry = AssetRegistry(MANIFEST)

    asset = registry.resolve_player("A", "libero", "Defense Ready", character_view=VIEW)

    assert asset["visualStyle"] == "professional"
    assert asset["view"] == VIEW
    assert asset["releaseStatus"] == "released"
