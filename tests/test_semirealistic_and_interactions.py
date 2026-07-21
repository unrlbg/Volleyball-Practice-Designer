from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
APP_JS = STATIC / "js" / "app.js"
INTERACTION_JS = STATIC / "js" / "interaction.js"


def test_professional_is_manifest_and_editor_default():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = APP_JS.read_text(encoding="utf-8")
    assert payload["defaultPlayerVisualStyle"] == "professional"
    assert 'visualStyle: "professional"' in source
    assert 'manifestDefaultPlayerStyle = "professional"' in source


def test_asset_api_advertises_professional_default(client):
    response = client.get("/api/assets")
    assert response.status_code == 200
    assert response.json()["defaultPlayerVisualStyle"] == "professional"


def test_at_least_fourteen_independent_transparent_runtime_assets_exist():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = [a for a in payload["assets"] if a.get("visualStyle") == "semi_realistic"]
    assert len(assets) >= 14
    assert len({a["asset"] for a in assets}) == len(assets)
    for asset in assets:
        path = STATIC / asset["asset"].removeprefix("/static/")
        thumb = STATIC / asset["thumbnail"].removeprefix("/static/")
        assert path.is_file() and path.suffix == ".webp"
        assert thumb.is_file() and thumb.suffix == ".webp"
        assert path.read_bytes()[8:12] == b"WEBP"
        assert b"ALPH" in path.read_bytes()[:80]
        assert asset["anchor"] == {"x": 0.5, "y": 1.0}


def test_resolver_is_professional_even_for_legacy_style_requests():
    registry = AssetRegistry(MANIFEST)
    assert registry.resolve_player("A", "Setter", "Ready")["visualStyle"] == "professional"
    assert registry.resolve_player("A", "Setter", "Ready", "legacy_vector")["id"] == "professional_female_athlete_01_ready"
    mapped = registry.resolve_player("A", "Setter", "Transition")
    assert mapped["id"] == "professional_female_athlete_01_ready"


def test_approved_toolbar_defaults_are_professional_for_both_teams():
    registry = AssetRegistry(MANIFEST)
    defaults = {
        "Setter": "Ready",
        "Libero": "Reception",
        "Middle": "Block",
        "Outside": "Reception",
    }
    for role, pose in defaults.items():
        assert registry.resolve_player("A", role, pose)["visualStyle"] == "professional"
        assert registry.resolve_player("B", role, pose)["visualStyle"] == "professional"
        assert registry.resolve_player("B", role, pose)["team"] == "B"
    assert registry.resolve_player("Neutral", "Coach", "Holding Ball")["visualStyle"] == "professional"


def test_toolbar_picker_placed_and_export_share_manifest_asset_resolution_contract():
    source = APP_JS.read_text(encoding="utf-8")
    assert "heroDefaults[item.role]" in source
    assert 'data-asset-id", asset.id' in source
    assert 'src="${asset.thumbnail}"' in source
    assert 'href="${asset.asset}"' in source
    assert "clone.querySelectorAll(\"image.visual-asset\")" in source


def test_raster_svg_drawings_and_text_use_unified_object_drag_binding():
    source = APP_JS.read_text(encoding="utf-8")
    assert 'class="drag-surface" data-drag-surface="raster"' in source
    assert 'data-drag-surface="arrow"' in source
    assert 'data-drag-surface="shape"' in source
    assert 'data-drag-surface="text"' in source
    assert 'e.target.closest(".object-hit")' in source
    assert "window.VPDInteraction.canMove(o)" in source


def test_zoom_aware_coordinate_conversion_for_required_levels():
    def convert(screen_x: float, pan_x: float, zoom: float) -> float:
        return (screen_x - pan_x) / zoom

    for zoom in (0.25, 0.5, 1, 2, 3):
        start = convert(420, 120, zoom)
        end = convert(420 + 60 * zoom, 120, zoom)
        assert end - start == 60
    source = INTERACTION_JS.read_text(encoding="utf-8")
    assert "(point.x - panX) / zoom" in source
    assert "(point.y - panY) / zoom" in source


def test_lock_contract_and_pointer_capture_cleanup():
    interaction = INTERACTION_JS.read_text(encoding="utf-8")
    app = APP_JS.read_text(encoding="utf-8")
    assert "object.locked !== true" in interaction
    assert 'svg.addEventListener("pointercancel", finishPointer)' in app
    assert 'svg.addEventListener("lostpointercapture"' in app
    assert "releasePointerCapture" in app


def test_style_change_preserves_transform_and_movability_metadata():
    registry = AssetRegistry(MANIFEST)
    original = {
        "id": "p",
        "type": "player",
        "assetId": "a_setter_ready",
        "visualStyle": "legacy_vector",
        "team": "A",
        "role": "Setter",
        "pose": "Ready",
        "x": 123,
        "y": 456,
        "width": 88,
        "height": 177,
        "rotation": 31,
        "mirror": True,
        "scale": 1.4,
        "layer": 7,
        "courtId": "court-two",
        "locked": False,
    }
    changed = deepcopy(original)
    selected = registry.resolve_player("A", "Setter", "Ready", "semi_realistic")
    changed["assetId"] = selected["id"]
    changed["visualStyle"] = selected["visualStyle"]
    migrated = registry.migrate_object(changed)
    for key in ("x", "y", "width", "height", "rotation", "mirror", "scale", "layer", "courtId", "locked"):
        assert migrated[key] == original[key]


def test_save_reload_migrates_unlocked_semirealistic_player_to_professional(client):
    payload = {
        "metadata": {"name": "Movable realistic player"},
        "frames": [{
            "id": "f",
            "objects": [{
                "id": "p",
                "type": "player",
                "assetId": "team_a_setter_ready_semirealistic",
                "visualStyle": "semi_realistic",
                "team": "A",
                "role": "Setter",
                "pose": "Ready",
                "x": 400,
                "y": 400,
                "locked": False,
            }],
        }],
    }
    response = client.post("/api/drills", json=payload)
    loaded = client.get(f'/api/drills/{response.json()["id"]}').json()
    player = loaded["frames"][0]["objects"][0]
    assert player["assetId"] == "professional_female_athlete_01_ready"
    assert player["visualStyle"] == "professional"
    assert player["locked"] is False
