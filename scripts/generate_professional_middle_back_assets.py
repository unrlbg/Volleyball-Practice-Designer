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
CHARACTER_ID = "female_athlete_03"
ROLE = "middle"
TEAM = "A"
VIEW = "Back"
BASE_ID = "professional_team_a_middle"
POSES = [
    "Block Ready",
    "Single Block",
    "Single Block Left",
    "Single Block Right",
    "Moving Block",
    "Moving Block Left",
    "Moving Block Right",
    "Double Block",
    "Double Block Left",
    "Double Block Right",
    "Jump Block",
    "Jump Block Left",
    "Jump Block Right",
    "Jump Block Spread",
    "Jump Block Close",
    "Jump Block Angle Left",
    "Jump Block Angle Right",
    "Quick Block",
    "Quick Block Left",
    "Quick Block Right",
    "Block Follow Through",
    "Land After Block",
    "Transition After Block",
    "Quick Attack Ready",
    "First-Tempo Approach",
    "Takeoff",
    "Quick Attack",
    "Quick Attack Land",
    "Tip",
    "Roll Shot",
]


def key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def colors() -> dict[str, tuple[int, int, int, int]]:
    return {
        "jersey": (18, 91, 78, 255),
        "jersey_dark": (10, 58, 52, 255),
        "accent": (238, 183, 62, 255),
        "skin": (196, 132, 92, 255),
        "skin_shadow": (146, 88, 58, 255),
        "hair": (48, 30, 23, 255),
        "shorts": (16, 46, 44, 255),
        "pads": (24, 25, 25, 255),
        "socks": (246, 244, 238, 255),
        "shoes": (248, 247, 241, 255),
        "shoe_shadow": (180, 184, 178, 255),
    }


def variant(pose: str) -> dict[str, float | bool]:
    p = key(pose)
    return {
        "airborne": any(t in p for t in ("jump", "block", "takeoff", "attack", "tip", "shot")) and "ready" not in p and "land" not in p,
        "crouch": any(t in p for t in ("ready", "land", "transition")),
        "shift": -0.09 if p.endswith("_left") or "angle_left" in p else (0.09 if p.endswith("_right") or "angle_right" in p else 0.0),
        "angle": -9 if "angle_left" in p else (9 if "angle_right" in p else 0),
        "spread": 1.35 if "spread" in p or "double" in p else (0.72 if "close" in p or "quick_block" in p else 1.0),
        "compact": "quick_block" in p,
        "follow": "follow_through" in p,
        "approach": any(t in p for t in ("approach", "transition", "roll_shot")),
    }


def limb(draw: ImageDraw.ImageDraw, pts: list[tuple[float, float]], fill: tuple[int, int, int, int], width: int) -> None:
    draw.line(pts, fill=fill, width=width, joint="curve")
    r = width * 0.46
    for x, y in pts[1:]:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def gradient_poly(layer: Image.Image, points: list[tuple[float, float]], fill: tuple[int, int, int, int], shade: tuple[int, int, int, int]) -> None:
    mask = Image.new("L", layer.size, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.polygon(points, fill=255)
    grad = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grad)
    min_x = int(min(x for x, _ in points))
    max_x = int(max(x for x, _ in points))
    for x in range(max(0, min_x), min(layer.width, max_x + 1)):
        t = (x - min_x) / max(1, max_x - min_x)
        c = tuple(int(fill[i] * (1 - t * 0.28) + shade[i] * (t * 0.28)) for i in range(4))
        gdraw.line([(x, 0), (x, layer.height)], fill=c)
    layer.alpha_composite(Image.composite(grad, Image.new("RGBA", layer.size, (0, 0, 0, 0)), mask))


def draw_pose(pose: str, size: int = 1400) -> Image.Image:
    c = colors()
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    v = variant(pose)
    cx = size * (0.5 + float(v["shift"]))
    foot = size * (0.86 if not v["airborne"] else 0.75)
    if v["crouch"]:
        foot = size * 0.88
    body = size * (0.38 if not v["crouch"] else 0.32)
    top = foot - body - size * 0.18
    hip_y = foot - size * 0.24
    shoulder_w = size * (0.215 if not v["compact"] else 0.19)
    hip_w = size * 0.145
    arm_w = int(size * 0.036)
    leg_w = int(size * 0.044)

    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow, "RGBA")
    sdraw.ellipse([cx - size * 0.21, foot + size * 0.02, cx + size * 0.21, foot + size * 0.055], fill=(0, 0, 0, 48))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(size * 0.012)))

    # Legs, knee pads, socks, shoe backs.
    knee_y = foot - size * (0.19 if not v["airborne"] else 0.13)
    knee_dx = size * (0.095 if not v["compact"] else 0.075)
    if v["approach"]:
        knee_dx *= 1.35
    knees = [(cx - knee_dx, knee_y), (cx + knee_dx, knee_y + size * 0.01)]
    feet = [(cx - size * (0.17 if not v["airborne"] else 0.13), foot), (cx + size * (0.17 if not v["airborne"] else 0.13), foot + size * 0.005)]
    hips = [(cx - hip_w * 0.45, hip_y), (cx + hip_w * 0.45, hip_y)]
    for hip, knee, toe in ((hips[0], knees[0], feet[0]), (hips[1], knees[1], feet[1])):
        limb(draw, [hip, knee], c["skin"], leg_w)
        limb(draw, [knee, (toe[0], toe[1] - size * 0.065)], c["skin"], leg_w)
        draw.rounded_rectangle([knee[0] - size * 0.046, knee[1] - size * 0.030, knee[0] + size * 0.046, knee[1] + size * 0.034], radius=int(size * 0.018), fill=c["pads"])
        draw.rounded_rectangle([toe[0] - size * 0.040, toe[1] - size * 0.082, toe[0] + size * 0.040, toe[1] - size * 0.025], radius=int(size * 0.014), fill=c["socks"])
        draw.ellipse([toe[0] - size * 0.070, toe[1] - size * 0.035, toe[0] + size * 0.075, toe[1] + size * 0.030], fill=c["shoes"])
        draw.arc([toe[0] - size * 0.055, toe[1] - size * 0.026, toe[0] + size * 0.055, toe[1] + size * 0.034], 0, 180, fill=c["shoe_shadow"], width=int(size * 0.006))

    # Shorts and torso from behind.
    draw.polygon([(cx - hip_w, hip_y - size * 0.015), (cx + hip_w, hip_y - size * 0.015), (cx + hip_w * 0.78, hip_y + size * 0.085), (cx, hip_y + size * 0.045), (cx - hip_w * 0.78, hip_y + size * 0.085)], fill=c["shorts"])
    torso = [(cx - shoulder_w, top), (cx + shoulder_w, top), (cx + hip_w, hip_y), (cx - hip_w, hip_y)]
    gradient_poly(img, torso, c["jersey"], c["jersey_dark"])
    draw.line([(cx - shoulder_w * 0.78, top + size * 0.035), (cx - hip_w * 0.75, hip_y - size * 0.015)], fill=c["accent"], width=int(size * 0.018))
    draw.line([(cx + shoulder_w * 0.78, top + size * 0.035), (cx + hip_w * 0.75, hip_y - size * 0.015)], fill=c["accent"], width=int(size * 0.018))
    draw.arc([cx - size * 0.06, top - size * 0.015, cx + size * 0.06, top + size * 0.075], 0, 180, fill=(245, 244, 235, 155), width=int(size * 0.012))
    draw.line([(cx - shoulder_w * 0.45, top + size * 0.095), (cx + shoulder_w * 0.45, top + size * 0.095)], fill=(255, 255, 255, 48), width=int(size * 0.008))
    draw.line([(cx - shoulder_w * 0.32, top + size * 0.18), (cx + shoulder_w * 0.32, top + size * 0.19)], fill=(0, 0, 0, 28), width=int(size * 0.007))

    # Arms and hands: fully extended for block variants, lower for landing/ready.
    hand_y = top - size * (0.26 if v["airborne"] else 0.07)
    if v["crouch"]:
        hand_y = top + size * 0.11
    if v["follow"]:
        hand_y = top - size * 0.02
    spread = float(v["spread"])
    hand_dx = size * 0.155 * spread
    angle = math.radians(float(v["angle"]))
    hand_shift = math.sin(angle) * size * 0.09
    hands = [(cx - hand_dx + hand_shift, hand_y), (cx + hand_dx + hand_shift, hand_y + (size * 0.018 if v["angle"] else 0))]
    shoulders = [(cx - shoulder_w * 0.92, top + size * 0.035), (cx + shoulder_w * 0.92, top + size * 0.035)]
    for shoulder, hand, side in ((shoulders[0], hands[0], -1), (shoulders[1], hands[1], 1)):
        elbow = ((shoulder[0] + hand[0]) / 2 + side * size * 0.018, (shoulder[1] + hand[1]) / 2 + size * (0.025 if v["airborne"] else 0.055))
        limb(draw, [shoulder, elbow, hand], c["skin"], arm_w)
        palm_w = size * 0.030
        draw.ellipse([hand[0] - palm_w, hand[1] - palm_w * 1.15, hand[0] + palm_w, hand[1] + palm_w * 1.15], fill=c["skin"])
        for finger in range(5):
            fx = hand[0] + (finger - 2) * size * 0.010
            fy = hand[1] - size * (0.045 + 0.006 * abs(finger - 2))
            draw.line([(hand[0], hand[1] - size * 0.010), (fx, fy)], fill=c["skin"], width=int(size * 0.006))

    # Neck, head, ponytail from the rear.
    draw.rounded_rectangle([cx - size * 0.035, top - size * 0.055, cx + size * 0.035, top + size * 0.012], radius=int(size * 0.014), fill=c["skin"])
    head = (cx, top - size * 0.115)
    draw.ellipse([head[0] - size * 0.070, head[1] - size * 0.078, head[0] + size * 0.070, head[1] + size * 0.075], fill=c["skin"])
    draw.pieslice([head[0] - size * 0.083, head[1] - size * 0.095, head[0] + size * 0.083, head[1] + size * 0.074], 178, 362, fill=c["hair"])
    draw.rounded_rectangle([head[0] - size * 0.072, head[1] - size * 0.010, head[0] + size * 0.072, head[1] + size * 0.115], radius=int(size * 0.034), fill=c["hair"])
    draw.ellipse([head[0] - size * 0.030, head[1] + size * 0.085, head[0] + size * 0.045, head[1] + size * 0.190], fill=c["hair"])
    draw.line([(cx - shoulder_w, top + size * 0.01), (cx - hip_w, hip_y - size * 0.01)], fill=(255, 255, 255, 58), width=int(size * 0.006))

    if v["angle"] or v["approach"]:
        img = img.rotate(float(v["angle"]) + (-5 if v["approach"] else 0), resample=Image.Resampling.BICUBIC, center=(cx, foot), fillcolor=(0, 0, 0, 0))
    bbox = img.getbbox()
    if bbox:
        pad = int(size * 0.045)
        img = img.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(size, bbox[2] + pad), min(size, bbox[3] + pad)))
    return img


def save_versions(pose: str) -> tuple[str, str, str, int, int]:
    pose_key = key(pose)
    master_rel = f"/static/assets/characters/professional/team_a/middle_blocker/back/masters/{pose_key}.png"
    runtime_rel = f"/static/assets/characters/professional/team_a/middle_blocker/back/{pose_key}.webp"
    thumb_rel = f"/static/assets/character_thumbnails/professional/team_a/middle_blocker/back/{pose_key}.webp"
    for rel in (master_rel, runtime_rel, thumb_rel):
        (STATIC / rel.removeprefix("/static/")).parent.mkdir(parents=True, exist_ok=True)
    master = draw_pose(pose, 1400)
    master.save(STATIC / master_rel.removeprefix("/static/"), "PNG")
    runtime = master.copy()
    runtime.thumbnail((416, 480), Image.Resampling.LANCZOS)
    runtime.save(STATIC / runtime_rel.removeprefix("/static/"), "WEBP", lossless=True, quality=98)
    thumb = master.copy()
    thumb.thumbnail((140, 150), Image.Resampling.LANCZOS)
    thumb.save(STATIC / thumb_rel.removeprefix("/static/"), "WEBP", lossless=True, quality=96)
    return master_rel, runtime_rel, thumb_rel, runtime.width, runtime.height


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = data["assets"]
    by_role_pose_view = {
        (asset.get("team"), asset.get("role"), asset.get("pose"), asset.get("view")): asset
        for asset in assets
        if asset.get("category") == "player" and asset.get("visualStyle") == "professional"
    }
    template = next(asset for asset in assets if asset.get("id") == "professional_female_athlete_03_block_ready")
    added = 0
    updated = 0
    for pose in POSES:
        master, runtime, thumb, width, height = save_versions(pose)
        existing = by_role_pose_view.get((TEAM, ROLE, pose, VIEW))
        if existing is None:
            existing = deepcopy(template)
            existing["id"] = f"{BASE_ID}_{key(pose)}_back"
            existing["pose"] = pose
            existing["poseId"] = key(pose)
            existing["team"] = TEAM
            existing["role"] = ROLE
            existing["view"] = VIEW
            existing["characterView"] = VIEW
            existing["supportsMirror"] = False
            existing["facingSupport"] = []
            existing["mappedFromPose"] = None
            assets.append(existing)
            added += 1
        else:
            updated += 1
        existing.update(
            {
                "category": "player",
                "objectKind": "character",
                "characterId": CHARACTER_ID,
                "visualStyle": "professional",
                "approvalStatus": "approved",
                "uniform": "forest_green_gold_team_a",
                "asset": runtime,
                "master": master,
                "thumbnail": thumb,
                "defaultWidth": max(78, round(width / max(1, height) * 172)),
                "defaultHeight": 172 if "ready" in key(pose) or "land" in key(pose) else 200,
                "anchor": {"x": 0.5, "y": 1.0},
                "footAnchor": {"x": 0.5, "y": 1.0},
                "anchorMode": "feet",
                "landingReference": {"x": 0.5, "y": 1.0},
                "shadow": {"enabled": True, "offsetX": 0, "offsetY": 7, "blur": 7, "opacity": 0.22},
                "shadowOffset": {"x": 0, "y": 7},
                "supportsMirror": False,
                "facingSupport": [],
                "professionalGrade": True,
                "containsNet": False,
                "containsCourt": False,
            }
        )
    data["schemaVersion"] = max(int(data.get("schemaVersion", 0)), 8)
    if "Middle Blocker Back View Pack" not in data.get("heroPack", {}).get("notes", []):
        data.setdefault("heroPack", {}).setdefault("notes", []).append("Middle Blocker Back View Pack")
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"updated={updated} added={added}")


if __name__ == "__main__":
    main()
