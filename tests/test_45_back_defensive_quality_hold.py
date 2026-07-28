from __future__ import annotations

import json
from pathlib import Path


from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
VIEW = "45° Back"
DEFENSIVE_GROUPS = {
    "General Defense",
    "Court Coverage",
    "Digging",
    "Diving",
    "After Defense",
}


def test_approved_45_back_defensive_assets_are_released():
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    generated = [
        asset for asset in raw["assets"]
        if asset.get("id", "").startswith("professional_45_back_")
    ]
    registry = AssetRegistry(MANIFEST)

    assert len(generated) == 162
    assert all(asset["visibleInEditor"] is True for asset in generated)
    assert all(asset["releaseStatus"] == "released" for asset in generated)
    assert all(asset["releaseState"] == "released" for asset in generated)
    assert all(asset["isReleased"] is True for asset in generated)
    assert all(asset["isApproved"] is True for asset in generated)
    assert len([
        asset for asset in registry.assets
        if asset.get("id", "").startswith("professional_45_back_")
    ]) == 162
    assert len([
        asset for asset in registry.library_assets
        if asset.get("id", "").startswith("professional_45_back_")
    ]) == 162


def test_defensive_pose_groups_remain_catalog_controlled_until_editor_palette_release():
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for role, groups in raw["professionalPoseGroups"].items():
        assert DEFENSIVE_GROUPS.isdisjoint(groups), role
    for role, poses in raw["professionalPoseCatalog"].items():
        assert "Defense Ready" not in poses, role
        assert "Forearm Dig" not in poses, role
        assert "Pancake" not in poses, role


def test_45_back_defensive_resolution_uses_released_assets():
    registry = AssetRegistry(MANIFEST)

    asset = registry.resolve_player("A", "libero", "Defense Ready", character_view=VIEW)

    assert asset["visualStyle"] == "professional"
    assert asset["view"] == VIEW
    assert asset["releaseStatus"] == "released"
