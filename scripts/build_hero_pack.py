"""Build the Professional-only character catalog and offline image tiers."""

from __future__ import annotations

import colorsys
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
ASSETS = STATIC / "assets"
ALPHA = ROOT / "work" / "hero_pack_alpha"
MANIFEST = ASSETS / "manifest.json"

CHARACTERS = {
    "setter": ("female_athlete_01", "balanced", "focused"),
    "outside": ("female_athlete_02", "powerful", "focused"),
    "opposite": ("female_athlete_05", "powerful", "focused"),
    "middle": ("female_athlete_03", "tall", "focused"),
    "libero": ("female_athlete_04", "compact", "focused"),
    "coach": ("coach_01", "lean", "calm"),
}

# Each visible pose explicitly maps to an approved identity-master pose. These
# mappings are temporary until a bespoke illustration passes art review.
POSE_CATALOG = {
    "setter": {
        "Ready": "ready",
        "Front Set": "front_set",
        "Back Set": "back_set",
    },
    "outside": {
        "Ready": "reception",
        "Reception": "reception",
        "Attack Start": "attack_start",
        "Approach Step 1": "approach_step_1",
        "Approach Step 2": "approach_step_2",
        "Takeoff": "takeoff",
        "Jump Attack": "jump_attack",
        "High Contact": "high_contact",
        "Line Attack": "line_attack",
        "Cross-Court Attack": "cross_court_attack",
        "Tip": "tip",
        "Roll Shot": "roll_shot",
        "Back-Row Attack": "back_row_attack",
        "Landing": "landing",
        "Transition After Attack": "transition_after_attack",
        "Block": "jump_attack",
        "Defense": "reception",
        "Cover": "reception",
        "Transition": "reception",
    },
    "opposite": {
        "Attack Start": "attack_start",
        "Approach Step 1": "approach_step_1",
        "Approach Step 2": "approach_step_2",
        "Takeoff": "takeoff",
        "Jump Attack": "jump_attack",
        "High Contact": "high_contact",
        "Line Attack": "line_attack",
        "Cross-Court Attack": "cross_court_attack",
        "Tip": "tip",
        "Roll Shot": "roll_shot",
        "Back-Row Attack": "back_row_attack",
        "Landing": "landing",
        "Transition After Attack": "transition_after_attack",
    },
    "middle": {
        "Ready": "block",
        "Block": "block",
        "Quick Attack Ready": "quick_attack_ready",
        "First-Tempo Approach": "first_tempo_approach",
        "Takeoff": "takeoff",
        "Front Quick Attack": "front_quick_attack",
        "Behind Setter Quick": "behind_setter_quick",
        "Gap Attack": "gap_attack",
        "Push Attack": "push_attack",
        "One-Foot Slide Approach": "one_foot_slide_approach",
        "Slide Approach": "one_foot_slide_approach",
        "One-Foot Slide Takeoff": "one_foot_slide_takeoff",
        "Slide Attack Contact": "slide_attack_contact",
        "Quick Approach": "first_tempo_approach",
        "Quick Attack": "front_quick_attack",
        "Slide Attack": "slide_attack_contact",
        "Landing": "landing",
        "Transition After Attack": "transition_after_attack",
        "Block Ready": "block",
        "Single Block": "block",
        "Moving Block": "block",
        "Transition": "block",
    },
    "libero": {
        "Reception": "reception",
        "Dig": "dig",
        "Dive": "dive",
    },
    "coach": {
        "Holding Ball": "holding_ball",
        "Tossing Ball": "tossing_ball",
    },
}

BASE_POSE_LABELS = {
    ("setter", "ready"): "Ready",
    ("setter", "front_set"): "Front Set",
    ("setter", "back_set"): "Back Set",
    ("outside", "reception"): "Reception",
    ("outside", "jump_attack"): "Jump Attack",
    ("outside", "attack_start"): "Attack Start",
    ("outside", "approach_step_1"): "Approach Step 1",
    ("outside", "approach_step_2"): "Approach Step 2",
    ("outside", "takeoff"): "Takeoff",
    ("outside", "high_contact"): "High Contact",
    ("outside", "line_attack"): "Line Attack",
    ("outside", "cross_court_attack"): "Cross-Court Attack",
    ("outside", "tip"): "Tip",
    ("outside", "roll_shot"): "Roll Shot",
    ("outside", "back_row_attack"): "Back-Row Attack",
    ("outside", "landing"): "Landing",
    ("outside", "transition_after_attack"): "Transition After Attack",
    ("opposite", "attack_start"): "Attack Start",
    ("opposite", "approach_step_1"): "Approach Step 1",
    ("opposite", "approach_step_2"): "Approach Step 2",
    ("opposite", "takeoff"): "Takeoff",
    ("opposite", "jump_attack"): "Jump Attack",
    ("opposite", "high_contact"): "High Contact",
    ("opposite", "line_attack"): "Line Attack",
    ("opposite", "cross_court_attack"): "Cross-Court Attack",
    ("opposite", "tip"): "Tip",
    ("opposite", "roll_shot"): "Roll Shot",
    ("opposite", "back_row_attack"): "Back-Row Attack",
    ("opposite", "landing"): "Landing",
    ("opposite", "transition_after_attack"): "Transition After Attack",
    ("middle", "block"): "Block",
    ("middle", "quick_attack"): "Quick Attack",
    ("middle", "quick_attack_ready"): "Quick Attack Ready",
    ("middle", "first_tempo_approach"): "First-Tempo Approach",
    ("middle", "takeoff"): "Takeoff",
    ("middle", "front_quick_attack"): "Front Quick Attack",
    ("middle", "behind_setter_quick"): "Behind Setter Quick",
    ("middle", "one_foot_slide_approach"): "One-Foot Slide Approach",
    ("middle", "one_foot_slide_takeoff"): "One-Foot Slide Takeoff",
    ("middle", "slide_attack_contact"): "Slide Attack Contact",
    ("middle", "gap_attack"): "Gap Attack",
    ("middle", "push_attack"): "Push Attack",
    ("middle", "landing"): "Landing",
    ("middle", "transition_after_attack"): "Transition After Attack",
    ("libero", "reception"): "Reception",
    ("libero", "dig"): "Dig",
    ("libero", "dive"): "Dive",
    ("coach", "holding_ball"): "Holding Ball",
    ("coach", "tossing_ball"): "Tossing Ball",
}

POSE_GROUPS = {
    "outside": {
        "Ready": ["Ready"],
        "Reception": ["Reception"],
        "Attack": [
            "Attack Start", "Approach Step 1", "Approach Step 2", "Takeoff",
            "Jump Attack", "High Contact", "Line Attack", "Cross-Court Attack",
            "Tip", "Roll Shot", "Back-Row Attack",
        ],
        "Block": ["Block"],
        "Defense": ["Defense", "Cover"],
        "Transition": ["Landing", "Transition After Attack", "Transition"],
    },
    "opposite": {
        "Ready": [],
        "Attack": [
            "Attack Start", "Approach Step 1", "Approach Step 2", "Takeoff",
            "Jump Attack", "High Contact", "Line Attack", "Cross-Court Attack",
            "Tip", "Roll Shot", "Back-Row Attack",
        ],
        "Block": [],
        "Defense": [],
        "Transition": ["Landing", "Transition After Attack"],
    },
    "middle": {
        "Ready": ["Ready", "Quick Attack Ready"],
        "Quick Attack": [
            "First-Tempo Approach", "Takeoff", "Front Quick Attack",
            "Behind Setter Quick", "Gap Attack", "Push Attack",
            "Quick Approach", "Quick Attack",
        ],
        "Slide Attack": [
            "One-Foot Slide Approach", "Slide Approach",
            "One-Foot Slide Takeoff", "Slide Attack Contact", "Slide Attack",
        ],
        "Block": ["Block", "Block Ready", "Single Block", "Moving Block"],
        "Transition": ["Landing", "Transition After Attack", "Transition"],
    },
}

AIRBORNE_POSES = {
    "takeoff", "jump_attack", "high_contact", "line_attack",
    "cross_court_attack", "tip", "roll_shot", "back_row_attack",
    "front_quick_attack", "behind_setter_quick", "one_foot_slide_takeoff",
    "slide_attack_contact", "gap_attack", "push_attack", "quick_attack",
}
ONE_FOOT_POSES = {"one_foot_slide_takeoff", "slide_attack_contact"}

TEAM_UNIFORMS = {
    "A": "forest_green_gold_team_a",
    "B": "dark_blue_light_blue_team_b",
    "libero": "burnt_orange_cream_libero",
    "Neutral": "charcoal_green_gold_coach",
}


def key(value: str) -> str:
    return value.lower().replace("-", " ").replace(" ", "_")


def trimmed(source: Path) -> Image.Image:
    image = Image.open(source).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if not bbox:
        raise ValueError(f"No visible pixels in {source}")
    image = image.crop(bbox)
    pad = max(8, round(max(image.size) * 0.025))
    canvas = Image.new("RGBA", (image.width + pad * 2, image.height + pad * 2))
    canvas.alpha_composite(image, (pad, pad))
    return canvas


def resized(image: Image.Image, max_height: int, max_width: int | None = None) -> Image.Image:
    scale = min(1, max_height / image.height)
    if max_width:
        scale = min(scale, max_width / image.width)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def save_webp(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "WEBP", lossless=True, method=6)


def team_b_recolor(image: Image.Image) -> Image.Image:
    """Convert green/gold team fabric to dark/light blue without changing skin."""
    result = image.convert("RGBA")
    pixels = []
    for red, green, blue, alpha in result.get_flattened_data():
        if not alpha:
            pixels.append((red, green, blue, alpha))
            continue
        hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        degrees = hue * 360
        # Forest-green jersey and shorts -> deep professional navy.
        if 75 <= degrees <= 175 and saturation >= 0.34 and value <= 0.72:
            hue = 216 / 360
            saturation = max(0.62, min(0.88, saturation))
            value = max(0.22, min(0.58, value))
        # Highly saturated gold fabric trim -> light blue. The saturation guard
        # intentionally excludes natural skin tones.
        elif 35 <= degrees <= 62 and saturation >= 0.72 and value >= 0.48:
            hue = 198 / 360
            saturation = 0.58
            value = max(0.62, min(0.88, value))
        nr, ng, nb = colorsys.hsv_to_rgb(hue, saturation, value)
        pixels.append((round(nr * 255), round(ng * 255), round(nb * 255), alpha))
    result.putdata(pixels)
    return result


def asset_record(
    *,
    character_id: str,
    role: str,
    pose: str,
    source_pose_id: str,
    team: str,
    body_type: str,
    expression: str,
    runtime_rel: str,
    master_rel: str,
    thumb_rel: str,
    runtime: Image.Image,
) -> dict:
    pose_id = key(pose)
    if role == "coach":
        display_height = 158
    elif source_pose_id in AIRBORNE_POSES:
        display_height = 174
    else:
        display_height = 154
    display_width = max(54, round(display_height * runtime.width / runtime.height))
    exact = BASE_POSE_LABELS[(role, source_pose_id)] == pose
    if source_pose_id in ONE_FOOT_POSES:
        anchor = {"x": 0.32, "y": 0.92}
        foot_anchor = {"x": 0.32, "y": 0.92}
        anchor_mode = "takeoff_foot"
    elif source_pose_id in AIRBORNE_POSES:
        anchor = {"x": 0.5, "y": 0.76}
        foot_anchor = {"x": 0.5, "y": 0.96}
        anchor_mode = "body_center_landing_reference"
    else:
        anchor = {"x": 0.5, "y": 1.0}
        foot_anchor = anchor.copy()
        anchor_mode = "feet"
    asset_id = (
        f"professional_{character_id}_{pose_id}"
        if team in {"A", "Neutral"}
        else f"professional_team_b_{character_id}_{pose_id}"
    )
    return {
        "id": asset_id,
        "category": "player",
        "objectKind": "character",
        "characterId": character_id,
        "visualStyle": "professional",
        "approvalStatus": "approved",
        "role": role,
        "pose": pose,
        "poseId": pose_id,
        "team": team,
        "uniform": TEAM_UNIFORMS["libero"] if role == "libero" else TEAM_UNIFORMS[team],
        "bodyType": body_type,
        "expression": expression,
        "footwear": "white_gold_court_shoes",
        "asset": runtime_rel,
        "master": master_rel,
        "thumbnail": thumb_rel,
        "defaultWidth": display_width,
        "defaultHeight": display_height,
        "anchor": anchor,
        "footAnchor": foot_anchor,
        "anchorMode": anchor_mode,
        "landingReference": foot_anchor,
        "shadow": {"enabled": True, "offsetX": 0, "offsetY": 7, "blur": 7, "opacity": 0.22},
        "shadowOffset": {"x": 0, "y": 7},
        "supportsMirror": True,
        "facingSupport": ["left", "right"],
        "mappedFromPose": None if exact else BASE_POSE_LABELS[(role, source_pose_id)],
    }


def build() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload["schemaVersion"] = max(6, payload.get("schemaVersion", 1))
    payload["defaultPlayerVisualStyle"] = "professional"
    payload["professionalPoseCatalog"] = {
        role: list(poses) for role, poses in POSE_CATALOG.items()
    }
    payload["professionalPoseGroups"] = POSE_GROUPS
    payload["hiddenProfessionalRoles"] = ["generic"]
    payload["heroPack"] = {
        "version": 2,
        "approvalStatus": "approved",
        "characterCount": 6,
        "identityMasterPoseCount": len(BASE_POSE_LABELS),
        "visiblePoseCount": sum(len(poses) for poses in POSE_CATALOG.values()),
        "teams": ["A", "B"],
    }
    payload["assets"] = [
        item for item in payload["assets"]
        if item.get("visualStyle") != "professional"
    ]
    for item in payload["assets"]:
        if item.get("visualStyle") == "legacy_vector":
            item["asset"] = item["asset"].replace(
                "/static/assets/players/legacy/",
                "/static/assets/characters/legacy/",
            )

    processed: dict[tuple[str, str, str], tuple[str, str, str, Image.Image]] = {}
    approved = []
    for role, pose_map in POSE_CATALOG.items():
        character_id, body_type, expression = CHARACTERS[role]
        teams = ["Neutral"] if role == "coach" else ["A", "B"]
        for source_pose_id in dict.fromkeys(pose_map.values()):
            source = ALPHA / f"{character_id}_{source_pose_id}.png"
            base_image = trimmed(source)
            for team in teams:
                image = (
                    team_b_recolor(base_image)
                    if team == "B" and role not in {"libero", "coach"}
                    else base_image.copy()
                )
                team_folder = "team_b" if team == "B" else "team_a" if team == "A" else "neutral"
                character_root = ASSETS / "characters" / "professional" / character_id / team_folder
                master_rel = (
                    f"/static/assets/characters/professional/{character_id}/{team_folder}/masters/"
                    f"{source_pose_id}.webp"
                )
                runtime_rel = (
                    f"/static/assets/characters/professional/{character_id}/{team_folder}/"
                    f"{source_pose_id}.webp"
                )
                thumb_rel = (
                    f"/static/assets/character_thumbnails/professional/{character_id}/{team_folder}/"
                    f"{source_pose_id}.webp"
                )
                master = resized(image, 1200)
                runtime = resized(image, 480)
                thumb = resized(image, 150, 180)
                save_webp(master, character_root / "masters" / f"{source_pose_id}.webp")
                save_webp(runtime, character_root / f"{source_pose_id}.webp")
                save_webp(
                    thumb,
                    ASSETS / "character_thumbnails" / "professional" / character_id
                    / team_folder / f"{source_pose_id}.webp",
                )
                processed[(role, source_pose_id, team)] = (
                    runtime_rel, master_rel, thumb_rel, runtime
                )

        for pose, source_pose_id in pose_map.items():
            for team in teams:
                runtime_rel, master_rel, thumb_rel, runtime = processed[
                    (role, source_pose_id, team)
                ]
                approved.append(asset_record(
                    character_id=character_id,
                    role=role,
                    pose=pose,
                    source_pose_id=source_pose_id,
                    team=team,
                    body_type=body_type,
                    expression=expression,
                    runtime_rel=runtime_rel,
                    master_rel=master_rel,
                    thumb_rel=thumb_rel,
                    runtime=runtime,
                ))

    payload["assets"].extend(approved)
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(approved)} Professional-only role/team/pose records.")


if __name__ == "__main__":
    build()
