from __future__ import annotations

import json
import math
import re
from copy import deepcopy
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
VIEW = "45° Back"
VIEW_SLUG = "45_back"

POSE_GROUPS = {
    "General Defense": [
        "Defense Ready",
        "Defensive Shuffle",
        "Split Step",
        "Low Defensive Position",
        "Left Defensive Position",
        "Right Defensive Position",
        "Deep Defense",
        "Mid Defense",
        "Short Defense",
    ],
    "Court Coverage": [
        "Line Defense",
        "Cross-Court Defense",
        "Cover Behind Block",
        "Pipe Defense",
        "Transition Defense",
    ],
    "Digging": [
        "Forearm Dig",
        "One Knee Dig",
        "Side Lunge Dig",
        "Split Dig",
        "Emergency Dig",
    ],
    "Diving": [
        "Forward Dive",
        "Side Dive",
        "Pancake",
        "Sprawl Defense",
        "Roll Recovery",
    ],
    "After Defense": ["Get Up", "Transition", "Ready Again"],
}
POSES = [pose for poses in POSE_GROUPS.values() for pose in poses]

ROLES = {
    "setter": ("female_athlete_01", "A", "team_a", "balanced", 1.00, (205, 137, 91), (54, 32, 24)),
    "outside": ("female_athlete_02", "A", "team_a", "power", 1.03, (198, 124, 82), (45, 28, 20)),
    "opposite": ("female_athlete_05", "A", "team_a", "tall_power", 1.05, (207, 132, 88), (42, 30, 22)),
    "middle": ("female_athlete_03", "A", "team_a", "tall", 1.08, (210, 142, 94), (58, 36, 24)),
    "libero": ("female_athlete_04", "A", "team_a", "compact", 0.96, (202, 128, 84), (49, 31, 23)),
    "coach": ("coach_01", "Neutral", "neutral", "coach", 1.02, (198, 132, 91), (42, 38, 34)),
}

BASE_COLORS = {
    "jersey": (18, 84, 72),
    "shorts": (15, 55, 50),
    "accent": (241, 193, 64),
    "knee": (20, 20, 20),
    "shoe": (250, 249, 242),
}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def rgba(c: tuple[int, int, int], a: int = 255) -> tuple[int, int, int, int]:
    return (*c, a)


def line(draw: ImageDraw.ImageDraw, pts, fill, width: int) -> None:
    draw.line(pts, fill=fill, width=width, joint="curve")
    radius = max(2, width // 2)
    for point in pts:
        draw.ellipse(
            [point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius],
            fill=fill,
        )


def capsule(draw: ImageDraw.ImageDraw, p1, p2, width: int, color, outline=None) -> None:
    if outline:
        line(draw, [p1, p2], outline, width + 8)
    line(draw, [p1, p2], color, width)
    highlight = rgba(lerp(color[:3], (255, 235, 210), 0.28), 110)
    offset = (-width * 0.13, -width * 0.18)
    line(
        draw,
        [(p1[0] + offset[0], p1[1] + offset[1]), (p2[0] + offset[0], p2[1] + offset[1])],
        highlight,
        max(2, width // 5),
    )


def pose_spec(pose: str) -> dict[str, object]:
    key = slug(pose)
    spec: dict[str, object] = {
        "crouch": 0.45,
        "lean": 0.0,
        "spread": 1.0,
        "step": 0.0,
        "arms": "ready",
        "low": 0,
        "dive": False,
        "kneel": False,
        "roll": False,
    }
    if "shuffle" in key:
        spec.update(step=-0.20, arms="balance")
    if "split_step" in key:
        spec.update(crouch=0.55, spread=1.22, arms="wide")
    if "low" in key:
        spec.update(crouch=0.72, spread=1.18, arms="low")
    if "left" in key or "line_defense" in key:
        spec.update(lean=-0.18, step=-0.24, arms="left_ready")
    if "right" in key or "cross_court" in key:
        spec.update(lean=0.18, step=0.24, arms="right_ready")
    if "deep" in key:
        spec.update(crouch=0.35, arms="ready")
    if "mid" in key:
        spec.update(crouch=0.50)
    if "short" in key:
        spec.update(crouch=0.65, arms="low")
    if "cover" in key or "pipe" in key:
        spec.update(crouch=0.58, arms="platform")
    if "transition_defense" in key:
        spec.update(crouch=0.45, step=0.20, arms="run_ready")
    if "forearm" in key:
        spec.update(crouch=0.62, arms="platform")
    if "one_knee" in key:
        spec.update(crouch=0.78, kneel=True, arms="platform")
    if "side_lunge" in key:
        spec.update(crouch=0.68, lean=-0.32, step=-0.42, arms="platform_left")
    if "split_dig" in key:
        spec.update(crouch=0.78, spread=1.55, arms="platform")
    if "emergency" in key:
        spec.update(crouch=0.72, lean=0.30, step=0.38, arms="reach_right")
    if "forward_dive" in key:
        spec.update(dive=True, lean=0.05, arms="dive_forward")
    if "side_dive" in key:
        spec.update(dive=True, lean=-0.45, arms="dive_left")
    if "pancake" in key:
        spec.update(dive=True, low=1, arms="pancake")
    if "sprawl" in key:
        spec.update(dive=True, low=1, spread=1.35, arms="sprawl")
    if "roll_recovery" in key:
        spec.update(crouch=0.75, roll=True, lean=0.35, arms="recover")
    if "get_up" in key:
        spec.update(crouch=0.70, kneel=True, arms="push_up")
    if key == "transition":
        spec.update(crouch=0.38, step=0.28, arms="run_ready")
    if "ready_again" in key:
        spec.update(crouch=0.48, arms="ready")
    return spec


def draw_figure(role: str, cfg: dict[str, object], pose: str, out: Path) -> tuple[int, int]:
    scale = 4
    width, height = 420, 700
    image = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    colors = {**BASE_COLORS, "skin": cfg["skin"], "hair": cfg["hair"]}  # type: ignore[index]
    spec = pose_spec(pose)
    hmul = float(cfg["height"])
    base_y = 630 * scale
    center_x = (210 + float(spec["lean"]) * 55) * scale
    body_height = 360 * hmul * scale
    crouch = float(spec["crouch"])
    if spec["dive"]:
        body_angle = (-25 if float(spec["lean"]) <= 0 else 20) * math.pi / 180
        torso_len = 175 * scale
        hip = (center_x + float(spec["lean"]) * 90 * scale, base_y - 155 * scale)
        shoulder = (hip[0] - math.sin(body_angle) * torso_len, hip[1] - math.cos(body_angle) * torso_len)
        head = (shoulder[0] - math.sin(body_angle) * 45 * scale, shoulder[1] - math.cos(body_angle) * 45 * scale)
    else:
        hip = (center_x + float(spec["lean"]) * 30 * scale, base_y - (70 + 70 * crouch) * scale)
        shoulder = (center_x + float(spec["lean"]) * 12 * scale, hip[1] - body_height * (0.43 - 0.08 * crouch))
        head = (shoulder[0] - 8 * scale, shoulder[1] - 58 * scale)

    left_shoulder = (shoulder[0] - 48 * scale, shoulder[1] + 12 * scale)
    right_shoulder = (shoulder[0] + 60 * scale, shoulder[1] + 26 * scale)
    left_hip = (hip[0] - 42 * scale, hip[1] + 22 * scale)
    right_hip = (hip[0] + 48 * scale, hip[1] + 28 * scale)
    spread = float(spec["spread"])
    step = float(spec["step"])
    left_knee = (left_hip[0] - (42 * spread - 20 * step) * scale, left_hip[1] + (95 - 45 * crouch) * scale)
    right_knee = (right_hip[0] + (42 * spread + 20 * step) * scale, right_hip[1] + (100 - 45 * crouch) * scale)
    left_foot = (left_knee[0] - (20 + 35 * abs(step)) * scale, base_y)
    right_foot = (right_knee[0] + (20 + 35 * abs(step)) * scale, base_y - 8 * scale)
    if spec["kneel"]:
        left_knee = (left_hip[0] - 35 * scale, base_y - 80 * scale)
        left_foot = (left_knee[0] - 50 * scale, base_y - 8 * scale)
        right_knee = (right_hip[0] + 65 * scale, base_y - 28 * scale)
        right_foot = (right_knee[0] + 35 * scale, base_y - 4 * scale)
    if spec["dive"]:
        left_knee = (left_hip[0] - 70 * scale, hip[1] + 105 * scale)
        right_knee = (right_hip[0] + 88 * scale, hip[1] + 105 * scale)
        left_foot = (left_knee[0] - 95 * scale, left_knee[1] + 55 * scale)
        right_foot = (right_knee[0] + 105 * scale, right_knee[1] + 45 * scale)
        if spec["low"]:
            left_foot = (left_knee[0] - 120 * scale, left_knee[1] + 15 * scale)
            right_foot = (right_knee[0] + 120 * scale, right_knee[1] + 18 * scale)

    arm = str(spec["arms"])
    left_elbow = (left_shoulder[0] - 42 * scale, left_shoulder[1] + 78 * scale)
    right_elbow = (right_shoulder[0] + 44 * scale, right_shoulder[1] + 72 * scale)
    left_hand = (left_elbow[0] + 18 * scale, left_elbow[1] + 55 * scale)
    right_hand = (right_elbow[0] - 16 * scale, right_elbow[1] + 55 * scale)
    if arm in {"platform", "platform_left"}:
        left_elbow = (left_shoulder[0] - 18 * scale, left_shoulder[1] + 80 * scale)
        right_elbow = (right_shoulder[0] + 18 * scale, right_shoulder[1] + 72 * scale)
        join = (center_x + (-35 if arm == "platform_left" else 0) * scale, hip[1] + 68 * scale)
        left_hand = (join[0] - 12 * scale, join[1] + 8 * scale)
        right_hand = (join[0] + 16 * scale, join[1] + 8 * scale)
    elif arm == "low":
        left_hand = (center_x - 34 * scale, hip[1] + 95 * scale)
        right_hand = (center_x + 38 * scale, hip[1] + 92 * scale)
    elif arm == "wide":
        left_hand = (left_shoulder[0] - 80 * scale, left_shoulder[1] + 95 * scale)
        right_hand = (right_shoulder[0] + 82 * scale, right_shoulder[1] + 90 * scale)
    elif arm == "balance":
        left_hand = (left_shoulder[0] - 95 * scale, left_shoulder[1] + 65 * scale)
        right_hand = (right_shoulder[0] + 70 * scale, right_shoulder[1] + 92 * scale)
    elif arm == "left_ready":
        left_hand = (left_shoulder[0] - 72 * scale, left_shoulder[1] + 78 * scale)
        right_hand = (center_x + 20 * scale, hip[1] + 82 * scale)
    elif arm == "right_ready":
        left_hand = (center_x - 20 * scale, hip[1] + 85 * scale)
        right_hand = (right_shoulder[0] + 78 * scale, right_shoulder[1] + 72 * scale)
    elif arm == "reach_right":
        left_hand = (center_x - 24 * scale, hip[1] + 82 * scale)
        right_hand = (right_shoulder[0] + 118 * scale, right_shoulder[1] + 120 * scale)
    elif arm == "run_ready":
        left_hand = (left_shoulder[0] - 30 * scale, left_shoulder[1] + 45 * scale)
        right_hand = (right_shoulder[0] + 58 * scale, right_shoulder[1] + 35 * scale)
    elif arm.startswith("dive") or arm in {"pancake", "sprawl"}:
        left_hand = (head[0] - 120 * scale, head[1] + 100 * scale)
        right_hand = (head[0] + 95 * scale, head[1] + 115 * scale)
        left_elbow = (left_shoulder[0] - 80 * scale, left_shoulder[1] + 70 * scale)
        right_elbow = (right_shoulder[0] + 70 * scale, right_shoulder[1] + 80 * scale)
        if arm == "pancake":
            right_hand = (head[0] + 150 * scale, head[1] + 135 * scale)
    elif arm == "push_up":
        left_hand = (left_shoulder[0] - 70 * scale, base_y - 25 * scale)
        right_hand = (right_shoulder[0] + 65 * scale, base_y - 32 * scale)
    elif arm == "recover":
        left_hand = (left_shoulder[0] - 55 * scale, hip[1] + 90 * scale)
        right_hand = (right_shoulder[0] + 45 * scale, hip[1] + 42 * scale)

    outline = (8, 18, 18, 95)
    draw.ellipse([center_x - 105 * scale, base_y - 12 * scale, center_x + 130 * scale, base_y + 24 * scale], fill=(0, 0, 0, 38))
    for a, b, w in [(left_hip, left_knee, 26), (left_knee, left_foot, 23), (right_hip, right_knee, 30), (right_knee, right_foot, 26)]:
        capsule(draw, a, b, w * scale // 4, colors["skin"], outline)
    for point in [left_knee, right_knee]:
        draw.rounded_rectangle([point[0] - 22 * scale, point[1] - 12 * scale, point[0] + 24 * scale, point[1] + 18 * scale], radius=7 * scale, fill=rgba(colors["knee"], 235))
    for point in [left_foot, right_foot]:
        draw.rounded_rectangle([point[0] - 32 * scale, point[1] - 13 * scale, point[0] + 35 * scale, point[1] + 15 * scale], radius=10 * scale, fill=rgba(colors["shoe"], 250), outline=(210, 208, 198, 210), width=2 * scale)
        draw.line([point[0] - 18 * scale, point[1] + 6 * scale, point[0] + 20 * scale, point[1] + 8 * scale], fill=(190, 184, 170, 160), width=2 * scale)

    draw.polygon([left_hip, (hip[0], hip[1] + 18 * scale), right_hip, (right_hip[0] + 10 * scale, right_hip[1] + 62 * scale), (center_x + 8 * scale, hip[1] + 85 * scale), (left_hip[0] - 12 * scale, left_hip[1] + 58 * scale)], fill=rgba(colors["shorts"], 255), outline=outline)
    torso = [(left_shoulder[0] - 8 * scale, left_shoulder[1] - 4 * scale), (right_shoulder[0] + 18 * scale, right_shoulder[1] - 2 * scale), (right_hip[0] + 18 * scale, right_hip[1] + 8 * scale), (hip[0] + 8 * scale, hip[1] + 12 * scale), (left_hip[0] - 20 * scale, left_hip[1] + 8 * scale)]
    draw.polygon(torso, fill=rgba(colors["jersey"], 255), outline=outline)
    draw.polygon([(right_shoulder[0] + 5 * scale, right_shoulder[1] + 3 * scale), (right_shoulder[0] + 20 * scale, right_shoulder[1] + 14 * scale), (right_hip[0] + 14 * scale, right_hip[1] + 1 * scale), (right_hip[0] + 2 * scale, right_hip[1] - 3 * scale)], fill=rgba(colors["accent"], 245))
    draw.line([left_shoulder, (shoulder[0] + 20 * scale, shoulder[1] + 20 * scale), right_shoulder], fill=(255, 255, 255, 45), width=2 * scale)

    for a, b, hand, w in [(left_shoulder, left_elbow, left_hand, 20), (right_shoulder, right_elbow, right_hand, 22)]:
        capsule(draw, a, b, w * scale // 4, colors["skin"], outline)
        capsule(draw, b, hand, max(14, w - 4) * scale // 4, colors["skin"], outline)
        draw.ellipse([hand[0] - 8 * scale, hand[1] - 8 * scale, hand[0] + 9 * scale, hand[1] + 9 * scale], fill=rgba(colors["skin"], 255), outline=outline)

    draw.rounded_rectangle([head[0] - 15 * scale, head[1] + 34 * scale, head[0] + 15 * scale, head[1] + 68 * scale], radius=7 * scale, fill=rgba(colors["skin"], 255))
    draw.ellipse([head[0] - 34 * scale, head[1] - 12 * scale, head[0] + 36 * scale, head[1] + 56 * scale], fill=rgba(colors["skin"], 255), outline=outline)
    draw.pieslice([head[0] - 39 * scale, head[1] - 18 * scale, head[0] + 39 * scale, head[1] + 60 * scale], 178, 365, fill=rgba(colors["hair"], 255))
    draw.ellipse([head[0] + 4 * scale, head[1] + 50 * scale, head[0] + 48 * scale, head[1] + 138 * scale], fill=rgba(colors["hair"], 245))
    for i in range(8):
        x = head[0] + (8 + i * 5) * scale
        y = head[1] + (58 + i * 8) * scale
        draw.line([x, y, x + (14 - i) * scale, y + 45 * scale], fill=rgba(lerp(colors["hair"], (130, 92, 62), 0.35), 130), width=max(1, scale))
    if role == "coach":
        draw.rectangle([head[0] - 28 * scale, head[1] + 53 * scale, head[0] + 28 * scale, head[1] + 78 * scale], fill=rgba(colors["hair"], 245))

    image = image.filter(ImageFilter.UnsharpMask(radius=1.1, percent=115, threshold=3))
    bbox = image.getbbox()
    pad = 28 * scale
    if bbox:
        box = (max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(image.width, bbox[2] + pad), min(image.height, bbox[3] + pad))
        image = image.crop(box)
    target_width = max(360, image.width // 2)
    target_height = max(640, image.height // 2)
    if max(target_width, target_height) < 820:
        ratio = 820 / max(target_width, target_height)
        target_width = round(target_width * ratio)
        target_height = round(target_height * ratio)
    master = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    master.save(out)
    return master.size


def main() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = payload["assets"]
    new_prefix = "professional_45_back_"
    assets[:] = [asset for asset in assets if not asset.get("id", "").startswith(new_prefix)]
    templates = {}
    for role, values in ROLES.items():
        character_id, team, *_ = values
        templates[role] = next(
            asset for asset in assets
            if asset.get("category") == "player"
            and asset.get("visualStyle") == "professional"
            and asset.get("role") == role
            and asset.get("characterId") == character_id
            and asset.get("team") == team
            and (asset.get("view") in (None, "Front") or asset.get("characterView") in (None, "Front"))
        )
    created = []
    for role, values in ROLES.items():
        character_id, team, team_path, body_type, height, skin, hair = values
        cfg = {"height": height, "skin": skin, "hair": hair}
        for pose in POSES:
            pose_slug = slug(pose)
            base = STATIC / "assets" / "characters" / "professional" / character_id / team_path / "views" / pose_slug
            thumbs = STATIC / "assets" / "character_thumbnails" / "professional" / character_id / team_path / "views" / pose_slug
            master_path = base / "masters" / f"{VIEW_SLUG}.png"
            size = draw_figure(role, cfg, pose, master_path)
            master = Image.open(master_path).convert("RGBA")
            runtime = master.copy()
            runtime.thumbnail((300, 480), Image.Resampling.LANCZOS)
            runtime_path = base / f"{VIEW_SLUG}.webp"
            runtime.save(runtime_path, "WEBP", quality=92, method=6, lossless=False)
            thumbnail = master.copy()
            thumbnail.thumbnail((140, 150), Image.Resampling.LANCZOS)
            thumbs.mkdir(parents=True, exist_ok=True)
            thumb_path = thumbs / f"{VIEW_SLUG}.webp"
            thumbnail.save(thumb_path, "WEBP", quality=88, method=6, lossless=False)

            asset_id = (
                f"{new_prefix}{team.lower()}_{character_id}_{pose_slug}"
                if team != "Neutral"
                else f"{new_prefix}{character_id}_{pose_slug}"
            )
            item = deepcopy(templates[role])
            item.update({
                "id": asset_id,
                "category": "player",
                "objectKind": "character",
                "characterId": character_id,
                "visualStyle": "professional",
                "approvalStatus": "approved",
                "role": role,
                "pose": pose,
                "poseId": pose_slug,
                "team": team,
                "uniform": "forest_green_gold_team_a" if team != "Neutral" else "coach_neutral_black",
                "bodyType": body_type,
                "asset": "/static/" + str(runtime_path.relative_to(STATIC)).replace("\\", "/"),
                "master": "/static/" + str(master_path.relative_to(STATIC)).replace("\\", "/"),
                "thumbnail": "/static/" + str(thumb_path.relative_to(STATIC)).replace("\\", "/"),
                "defaultWidth": max(70, round(108 * size[0] / max(1, size[1]) * 1.7)),
                "defaultHeight": 125 if pose_spec(pose)["dive"] else 185,
                "anchor": {"x": 0.5, "y": 1.0},
                "footAnchor": {"x": 0.5, "y": 1.0},
                "anchorMode": "feet",
                "landingReference": {"x": 0.5, "y": 1.0},
                "shadow": {"enabled": True, "offsetX": 0, "offsetY": 7, "blur": 7, "opacity": 0.22},
                "shadowOffset": {"x": 0, "y": 7},
                "supportsMirror": False,
                "facingSupport": [],
                "mappedFromPose": None,
                "view": VIEW,
                "characterView": VIEW,
                "availableCharacterViews": [
                    "Front",
                    "3/4 Front Left",
                    "3/4 Front Right",
                    "Left Side",
                    "Right Side",
                    "3/4 Back Left",
                    "3/4 Back Right",
                    "Back",
                    VIEW,
                ],
                "professionalGrade": True,
                "containsNet": False,
                "containsCourt": False,
                "releaseStatus": "released",
                "visibleInEditor": True,
                "sourceQualityReference": "professional_45_back_defensive_library_v1",
                "cameraAngle": "45° rear defensive view",
            })
            assets.append(item)
            created.append(asset_id)

    views = payload.setdefault("professionalCharacterViews", [
        "Front",
        "3/4 Front Left",
        "3/4 Front Right",
        "Left Side",
        "Right Side",
        "3/4 Back Left",
        "3/4 Back Right",
        "Back",
    ])
    if VIEW not in views:
        views.append(VIEW)
    role_groups = payload.setdefault("professionalPoseGroups", {})
    for role in ROLES:
        groups = role_groups.setdefault(role, {})
        for group, poses in POSE_GROUPS.items():
            existing = [pose for pose in groups.get(group, []) if pose not in poses]
            groups[group] = existing + poses
    notes = payload.setdefault("heroPack", {}).setdefault("notes", [])
    if "45° Back Defensive Character Library" not in notes:
        notes.append("45° Back Defensive Character Library")
    MANIFEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"created {len(created)} 45-back defensive professional assets")
    print(created[:3])
    print(created[-3:])


if __name__ == "__main__":
    main()
