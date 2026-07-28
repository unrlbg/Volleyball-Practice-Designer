from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
APP_JS = STATIC / "js" / "app.js"

OUTSIDE_ATTACKS = [
    "Attack Start", "Approach Step 1", "Approach Step 2", "Takeoff",
    "Jump Attack", "High Contact", "Line Attack", "Cross-Court Attack",
    "Tip", "Roll Shot", "Back-Row Attack", "Landing",
    "Transition After Attack",
]
OPPOSITE_ATTACKS = OUTSIDE_ATTACKS.copy()
MIDDLE_ATTACKS = [
    "Quick Attack Ready", "First-Tempo Approach", "Takeoff",
    "Front Quick Attack", "Behind Setter Quick", "One-Foot Slide Approach",
    "One-Foot Slide Takeoff", "Slide Attack Contact", "Gap Attack",
    "Push Attack", "Landing", "Transition After Attack",
]


def registry() -> AssetRegistry:
    return AssetRegistry(MANIFEST)


def test_every_attacking_pose_resolves_to_exact_professional_team_asset():
    loaded = registry()
    for role, poses in (
        ("outside", OUTSIDE_ATTACKS),
        ("opposite", OPPOSITE_ATTACKS),
        ("middle", MIDDLE_ATTACKS),
    ):
        for team in ("A", "B"):
            for pose in poses:
                asset = loaded.resolve_player(team, role, pose)
                assert asset["visualStyle"] == "professional"
                assert asset["team"] == team
                assert asset["pose"] == pose
                assert asset["mappedFromPose"] is None
                assert (STATIC / asset["asset"].removeprefix("/static/")).is_file()
                assert (STATIC / asset["thumbnail"].removeprefix("/static/")).is_file()


def test_recurring_identity_is_stable_within_each_attacking_role():
    loaded = registry()
    expected = {
        "outside": "female_athlete_02",
        "opposite": "female_athlete_05",
        "middle": "female_athlete_03",
    }
    for role, poses in (
        ("outside", OUTSIDE_ATTACKS),
        ("opposite", OPPOSITE_ATTACKS),
        ("middle", MIDDLE_ATTACKS),
    ):
        for team in ("A", "B"):
            assert {
                loaded.resolve_player(team, role, pose)["characterId"]
                for pose in poses
            } == {expected[role]}
    assert expected["outside"] != expected["opposite"]


def test_team_change_preserves_pose_and_all_editor_transform_fields():
    loaded = registry()
    original = {
        "id": "attacker",
        "type": "character",
        "team": "A",
        "role": "Opposite",
        "pose": "Line Attack",
        "assetId": "professional_female_athlete_05_line_attack",
        "characterId": "female_athlete_05",
        "x": 401,
        "y": 287,
        "width": 111,
        "height": 174,
        "rotation": 43,
        "facing": "Left",
        "mirrorX": True,
        "opacity": 0.63,
        "zIndex": 8,
        "assignedCourtId": "court-b",
        "locked": True,
    }
    changed = deepcopy(original)
    changed["team"] = "B"
    changed["assetId"] = loaded.resolve_player(
        "B", changed["role"], changed["pose"]
    )["id"]
    migrated = loaded.migrate_object(changed)
    assert migrated["pose"] == "Line Attack"
    assert migrated["characterId"] == "female_athlete_05"
    assert migrated["assetId"] == "professional_team_b_female_athlete_05_line_attack"
    for field in (
        "x", "y", "width", "height", "rotation", "facing", "mirrorX",
        "opacity", "zIndex", "assignedCourtId", "locked",
    ):
        assert migrated[field] == original[field]


def test_airborne_and_one_foot_assets_use_reliable_anchor_modes():
    loaded = registry()
    for role, pose in (
        ("outside", "Jump Attack"),
        ("outside", "High Contact"),
        ("opposite", "Back-Row Attack"),
        ("middle", "Front Quick Attack"),
    ):
        asset = loaded.resolve_player("A", role, pose)
        assert asset["anchorMode"] == "body_center_landing_reference"
        assert asset["defaultHeight"] == 174
        assert asset["anchor"]["y"] < asset["landingReference"]["y"]
    for pose in ("One-Foot Slide Takeoff", "Slide Attack Contact"):
        asset = loaded.resolve_player("A", "middle", pose)
        assert asset["anchorMode"] == "takeoff_foot"
        assert asset["anchor"] == asset["footAnchor"]
        assert asset["anchor"]["x"] != 0.5


def test_horizontal_mirroring_is_supported_and_vertical_flip_is_hidden():
    loaded = registry()
    for role, pose in (
        ("outside", "Cross-Court Attack"),
        ("opposite", "Line Attack"),
        ("middle", "Slide Attack Contact"),
    ):
        asset = loaded.resolve_player("A", role, pose)
        assert asset["supportsMirror"] is True
        assert asset["facingSupport"] == ["left", "right"]
    source = APP_JS.read_text(encoding="utf-8")
    assert 'isCourt || isCharacter(o)' in source
    assert "if(!o||isCharacter(o))return" in source


def test_grouped_pose_picker_only_lists_manifest_backed_poses():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    groups = payload["professionalPoseGroups"]
    for role, role_groups in groups.items():
        catalog = set(payload["professionalPoseCatalog"][role])
        for poses in role_groups.values():
            for pose in poses:
                assert pose in catalog or any(
                    item.get("category") == "player"
                    and item.get("visualStyle") == "professional"
                    and item.get("role") == role
                    and item.get("pose") == pose
                    and item.get("visibleInEditor") is not False
                    and not str(item.get("releaseStatus", "released")).startswith("hidden")
                    for item in payload["assets"]
                )
    assert groups["outside"]["Attack"] == OUTSIDE_ATTACKS[:-2]
    assert groups["opposite"]["Attack"] == OPPOSITE_ATTACKS[:-2]
    assert "One-Foot Slide Approach" in groups["middle"]["Slide Attack"]
    source = APP_JS.read_text(encoding="utf-8")
    assert "professionalPoseGroups = payload.professionalPoseGroups" in source
    assert '<optgroup label="${escapeHtml(label)}">' in source


def test_save_reload_preserves_attacking_pose_identity_and_mirroring(client):
    payload = {
        "metadata": {"name": "Attacking pose persistence"},
        "frames": [{
            "id": "attack-frame",
            "objects": [{
                "id": "middle-slide",
                "type": "character",
                "team": "B",
                "role": "Middle",
                "pose": "Slide Attack Contact",
                "assetId": "professional_team_b_female_athlete_03_slide_attack_contact",
                "characterId": "female_athlete_03",
                "x": 510,
                "y": 330,
                "rotation": 18,
                "mirrorX": True,
                "flipY": False,
                "locked": False,
            }],
        }],
    }
    saved = client.post("/api/drills", json=payload)
    assert saved.status_code == 201
    loaded = client.get(f'/api/drills/{saved.json()["id"]}').json()
    player = loaded["frames"][0]["objects"][0]
    assert player["pose"] == "Slide Attack Contact"
    assert player["assetId"] == "professional_team_b_female_athlete_03_slide_attack_contact"
    assert player["characterId"] == "female_athlete_03"
    assert player["mirrorX"] is True
    assert player["flipY"] is False


def test_frame_and_court_duplication_keep_attacking_assets_independent():
    source = APP_JS.read_text(encoding="utf-8")
    assert "const c=deep(frame())" in source
    assert "o.id=uid()" in source
    assert "id: uid(), courtId: copy.id, assignedCourtId: copy.id" in source
    original = {
        "id": "one",
        "assetId": "professional_female_athlete_02_line_attack",
        "pose": "Line Attack",
    }
    copied = deepcopy(original)
    copied["id"] = "two"
    copied["pose"] = "Tip"
    assert original["id"] == "one"
    assert original["pose"] == "Line Attack"


def test_export_and_print_use_the_selected_attacking_raster_assets():
    source = APP_JS.read_text(encoding="utf-8")
    assert 'href="${asset.asset}"' in source
    assert 'clone.querySelectorAll("image.visual-asset")' in source
    assert "await waitForVisualAssets()" in source
    assert "function printDrill" in source
    assert "legacy_vector" not in source[source.index("function resolveAsset"):source.index("function equipmentAsset")]


def test_no_unbacked_attacking_pose_is_exposed():
    loaded = registry()
    payload = loaded.manifest()
    professional = [
        item for item in payload["assets"]
        if item.get("visualStyle") == "professional"
        and item.get("view") == "Front"
    ]
    for role, poses in payload["professionalPoseCatalog"].items():
        teams = ("Neutral",) if role == "coach" else ("A", "B")
        for team in teams:
            for pose in poses:
                matches = [
                    item for item in professional
                    if item["role"] == role and item["team"] == team
                    and item["pose"] == pose
                ]
                assert len(matches) == 1
