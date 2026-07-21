from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path

import pytest

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app" / "static" / "assets" / "manifest.json"
APP_JS = ROOT / "app" / "static" / "js" / "app.js"
INTERACTION_JS = ROOT / "app" / "static" / "js" / "interaction.js"
INDEX = ROOT / "app" / "templates" / "index.html"


@pytest.fixture(scope="module")
def registry() -> AssetRegistry:
    return AssetRegistry(MANIFEST)


def test_old_drills_default_safely_to_zero_rotation(registry):
    migrated = registry.migrate_drill({
        "frames": [{"id": "f1", "court": {"attackLines": True}, "objects": []}]
    })
    court = migrated["frames"][0]["courts"][0]
    assert court["rotation"] == 0
    assert court["rotateContentsWithCourt"] is False
    assert court["keepPlayersUpright"] is True


@pytest.mark.parametrize("rotation", [0, 45, 90, 180, 270, 315])
def test_court_rotation_preserves_eighteen_by_nine_ratio(registry, rotation):
    court = registry.default_court({"width": 918, "height": 123, "rotation": rotation})
    assert court["rotation"] == rotation
    assert court["height"] == court["width"] / 2


def test_court_rotation_and_settings_persist_through_api(client):
    payload = {
        "metadata": {"name": "Rotated court"},
        "frames": [{
            "id": "frame-rotation",
            "courts": [{
                "id": "court-rotation",
                "type": "court",
                "name": "Court 1",
                "x": 600,
                "y": 390,
                "width": 780,
                "height": 390,
                "rotation": 315,
                "rotateContentsWithCourt": True,
                "keepPlayersUpright": False,
                "settings": {},
            }],
            "objects": [],
        }],
    }
    created = client.post("/api/drills", json=payload)
    assert created.status_code == 201
    loaded = client.get(f'/api/drills/{created.json()["id"]}').json()
    court = loaded["frames"][0]["courts"][0]
    assert court["rotation"] == 315
    assert court["rotateContentsWithCourt"] is True
    assert court["keepPlayersUpright"] is False
    assert court["width"] / court["height"] == 2


def test_contents_rotate_around_court_center():
    center = (600, 390)
    point = (700, 390)
    radians = math.radians(90)
    rotated = (
        center[0] + (point[0] - center[0]) * math.cos(radians) - (point[1] - center[1]) * math.sin(radians),
        center[1] + (point[0] - center[0]) * math.sin(radians) + (point[1] - center[1]) * math.cos(radians),
    )
    assert rotated == pytest.approx((600, 490))
    source = APP_JS.read_text(encoding="utf-8")
    assert "rotatePoint(original, court, delta)" in source
    assert "object.x = point.x" in source
    assert "object.y = point.y" in source


def test_players_upright_and_rotating_modes_are_implemented():
    source = APP_JS.read_text(encoding="utf-8")
    assert '["player", "character"].includes(object.type) && court.keepPlayersUpright' in source
    assert "object.rotation = original.rotation" in source
    assert "original.rotation + delta" in source


def test_rotation_handle_free_snap_and_fine_rotation_contract():
    app = APP_JS.read_text(encoding="utf-8")
    interaction = INTERACTION_JS.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")
    assert '"data-handle": "rotate"' in app
    assert "startAngle:" in app
    assert "e.shiftKey" in app
    assert "Math.round(normalized / 15) * 15" in interaction
    assert "Math.round(normalized)" in interaction
    assert 'id="prop-rotation" type="number" min="0" max="359" step="1"' in html


def test_rotation_controls_and_keyboard_shortcuts_exist():
    app = APP_JS.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")
    for control_id in (
        "rotate-court-left",
        "rotate-court-right",
        "reset-court-rotation",
        "rotate-court-contents",
        "keep-players-upright",
    ):
        assert f'id="{control_id}"' in html
    assert 'e.altKey && (e.key === "ArrowLeft" || e.key === "ArrowRight")' in app
    assert "rotateSelectedCourtBy(-90)" in app
    assert "rotateSelectedCourtBy(90)" in app


def test_duplicated_courts_preserve_rotation_and_settings():
    original = {
        "id": "court-1",
        "rotation": 45,
        "rotateContentsWithCourt": True,
        "keepPlayersUpright": False,
        "width": 780,
        "height": 390,
    }
    duplicate = deepcopy(original)
    duplicate["id"] = "court-2"
    assert duplicate["rotation"] == 45
    assert duplicate["rotateContentsWithCourt"] is True
    assert duplicate["keepPlayersUpright"] is False
    source = APP_JS.read_text(encoding="utf-8")
    assert "const copy = deep(source);" in source


def test_export_and_print_clone_rendered_rotation():
    source = APP_JS.read_text(encoding="utf-8")
    assert "clone = svg.cloneNode(true)" in source
    assert "new XMLSerializer().serializeToString(clone)" in source
    assert "transform: `translate(${c.x} ${c.y}) rotate(${c.rotation})`" in source
    assert "window.print()" in source


def test_rotation_manifest_is_unchanged_and_valid():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["defaultPlayerVisualStyle"] == "professional"
