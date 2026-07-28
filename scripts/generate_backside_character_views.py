from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
BACKSIDE_VIEWS = (
    ("Back", "back"),
    ("3/4 Back Left", "three_quarter_back_left"),
    ("3/4 Back Right", "three_quarter_back_right"),
)
ALL_VIEWS = [
    "Front",
    "3/4 Front Left",
    "3/4 Front Right",
    "Left Side",
    "Right Side",
    "3/4 Back Left",
    "3/4 Back Right",
    "Back",
]


def key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def team_dir(team: str) -> str:
    return "neutral" if team == "Neutral" else ("team_b" if team == "B" else "team_a")


def palette(asset: dict) -> dict[str, str]:
    role = asset.get("role")
    if role == "coach":
        return {"jersey": "#394744", "side": "#f0b949", "shorts": "#202927", "hair": "#3b241b", "skin": "#c98f6b", "pad": "#f8f3e8", "shoe": "#f4f2ea"}
    if role == "libero":
        accent = "#176b62" if asset.get("team") == "A" else "#ef7d4d"
        return {"jersey": "#f4efe6", "side": accent, "shorts": "#123c38" if asset.get("team") == "A" else "#5d3027", "hair": "#332019", "skin": "#c98f6b", "pad": "#f4efe6", "shoe": "#f4f2ea"}
    if asset.get("team") == "B":
        return {"jersey": "#ef7d4d", "side": "#ffffff", "shorts": "#49251f", "hair": "#332019", "skin": "#c98f6b", "pad": "#f5efe8", "shoe": "#f4f2ea"}
    return {"jersey": "#176b62", "side": "#f0b949", "shorts": "#123c38", "hair": "#332019", "skin": "#c98f6b", "pad": "#f5efe8", "shoe": "#f4f2ea"}


def pose_flags(pose: str) -> tuple[bool, bool, bool, bool]:
    pose_key = key(pose)
    airborne = any(token in pose_key for token in ("jump", "takeoff", "attack", "contact", "block", "tip")) and "ready" not in pose_key and "start" not in pose_key
    crouch = any(token in pose_key for token in ("ready", "reception", "dig", "defensive", "cover"))
    dive = "dive" in pose_key
    setpose = "set" in pose_key or "tossing" in pose_key or "holding_ball" in pose_key
    return airborne, crouch, dive, setpose


def draw_backside(asset: dict, view: str, size: tuple[int, int]) -> Image.Image:
    width, height = size
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    colors = palette(asset)
    center_x = width / 2
    airborne, crouch, dive, setpose = pose_flags(asset.get("pose", ""))
    yaw = -1 if "Left" in view else (1 if "Right" in view else 0)
    lean = (-10 if any(token in key(asset.get("pose")) for token in ("approach", "transition")) else 0) + yaw * 8
    foot_y = height * (0.78 if airborne else 0.90)
    if dive:
        foot_y = height * 0.82
        lean = -28 + yaw * 8
    body_h = height * (0.35 if crouch else 0.42)
    if airborne:
        body_h = height * 0.44
    torso_top = foot_y - body_h - height * 0.20
    torso_bottom = foot_y - height * 0.28
    shoulder_w = width * (0.42 if dive else 0.36)
    hip_w = width * (0.34 if dive else 0.26)
    shift = yaw * width * 0.055

    shadow_y = foot_y + height * 0.035
    draw.ellipse([center_x - width * 0.30, shadow_y - height * 0.018, center_x + width * 0.30, shadow_y + height * 0.020], fill=(0, 0, 0, 35))

    hip_left = (center_x + shift - hip_w / 2, torso_bottom)
    hip_right = (center_x + shift + hip_w / 2, torso_bottom)
    if dive:
        knees = [(center_x - width * 0.22, foot_y - height * 0.13), (center_x + width * 0.16, foot_y - height * 0.04)]
        feet = [(center_x - width * 0.38, foot_y + height * 0.02), (center_x + width * 0.32, foot_y + height * 0.03)]
    elif airborne:
        knees = [(center_x - width * 0.16 + yaw * width * 0.03, foot_y - height * 0.13), (center_x + width * 0.14 + yaw * width * 0.05, foot_y - height * 0.06)]
        feet = [(center_x - width * 0.22 + yaw * width * 0.05, foot_y + height * 0.03), (center_x + width * 0.22 + yaw * width * 0.08, foot_y + height * 0.05)]
    elif crouch:
        knees = [(center_x - width * 0.20 + yaw * width * 0.02, foot_y - height * 0.18), (center_x + width * 0.20 + yaw * width * 0.04, foot_y - height * 0.17)]
        feet = [(center_x - width * 0.30 + yaw * width * 0.02, foot_y + height * 0.02), (center_x + width * 0.30 + yaw * width * 0.04, foot_y + height * 0.02)]
    else:
        knees = [(center_x - width * 0.12 + yaw * width * 0.02, foot_y - height * 0.20), (center_x + width * 0.12 + yaw * width * 0.04, foot_y - height * 0.19)]
        feet = [(center_x - width * 0.17 + yaw * width * 0.03, foot_y + height * 0.02), (center_x + width * 0.17 + yaw * width * 0.05, foot_y + height * 0.02)]

    for hip, knee, foot in ((hip_left, knees[0], feet[0]), (hip_right, knees[1], feet[1])):
        draw.line([hip, knee, foot], fill=colors["skin"], width=max(5, int(width * 0.055)))
        draw.rounded_rectangle([knee[0] - width * 0.055, knee[1] - height * 0.025, knee[0] + width * 0.055, knee[1] + height * 0.025], radius=int(width * 0.02), fill=colors["pad"])
        draw.ellipse([foot[0] - width * 0.075, foot[1] - height * 0.025, foot[0] + width * 0.075, foot[1] + height * 0.025], fill=colors["shoe"])
        draw.arc([foot[0] - width * 0.06, foot[1] - height * 0.025, foot[0] + width * 0.06, foot[1] + height * 0.035], 0, 180, fill=(130, 130, 130, 160), width=max(1, int(width * 0.01)))

    draw.polygon([(center_x + shift - hip_w * 0.62, torso_bottom - height * 0.015), (center_x + shift + hip_w * 0.62, torso_bottom - height * 0.015), (center_x + shift + hip_w * 0.48, torso_bottom + height * 0.10), (center_x + shift, torso_bottom + height * 0.045), (center_x + shift - hip_w * 0.48, torso_bottom + height * 0.10)], fill=colors["shorts"])
    torso = [(center_x + shift - shoulder_w / 2, torso_top), (center_x + shift + shoulder_w / 2, torso_top + height * 0.015), (center_x + shift + hip_w / 2, torso_bottom), (center_x + shift - hip_w / 2, torso_bottom)]
    draw.polygon(torso, fill=colors["jersey"])
    draw.line([(center_x + shift - shoulder_w * 0.35, torso_top + height * 0.04), (center_x + shift - hip_w * 0.34, torso_bottom - height * 0.02)], fill=colors["side"], width=max(2, int(width * 0.025)))
    draw.line([(center_x + shift + shoulder_w * 0.35, torso_top + height * 0.04), (center_x + shift + hip_w * 0.34, torso_bottom - height * 0.02)], fill=colors["side"], width=max(2, int(width * 0.025)))
    draw.arc([center_x + shift - width * 0.09, torso_top - height * 0.015, center_x + shift + width * 0.09, torso_top + height * 0.08], 0, 180, fill=(255, 255, 255, 120), width=max(2, int(width * 0.018)))
    draw.line([(center_x + shift - shoulder_w * 0.22, torso_top + height * 0.10), (center_x + shift + shoulder_w * 0.22, torso_top + height * 0.11)], fill=(255, 255, 255, 45), width=max(1, int(width * 0.01)))

    arm_raise = height * 0.18 if setpose or airborne else 0
    left_hand = (center_x - width * 0.36 + yaw * width * 0.04, torso_top + height * 0.16 - arm_raise)
    right_hand = (center_x + width * 0.36 + yaw * width * 0.04, torso_top + height * 0.16 - arm_raise * 0.85)
    if "block" in key(asset.get("pose")) or "high_contact" in key(asset.get("pose")):
        left_hand = (center_x - width * 0.24, torso_top - height * 0.18)
        right_hand = (center_x + width * 0.24, torso_top - height * 0.18)
    for shoulder, hand in (((center_x + shift - shoulder_w / 2, torso_top + height * 0.04), left_hand), ((center_x + shift + shoulder_w / 2, torso_top + height * 0.04), right_hand)):
        elbow = ((shoulder[0] + hand[0]) / 2 + yaw * width * 0.03, (shoulder[1] + hand[1]) / 2 + height * 0.04)
        draw.line([shoulder, elbow, hand], fill=colors["skin"], width=max(5, int(width * 0.05)))
        draw.ellipse([hand[0] - width * 0.035, hand[1] - width * 0.035, hand[0] + width * 0.035, hand[1] + width * 0.035], fill=colors["skin"])

    draw.rounded_rectangle([center_x + shift - width * 0.045, torso_top - height * 0.035, center_x + shift + width * 0.045, torso_top + height * 0.025], radius=int(width * 0.02), fill=colors["skin"])
    head = (center_x + shift + yaw * width * 0.035, torso_top - height * 0.105)
    draw.ellipse([head[0] - width * 0.105, head[1] - height * 0.105, head[0] + width * 0.105, head[1] + height * 0.100], fill=colors["skin"])
    draw.pieslice([head[0] - width * 0.13, head[1] - height * 0.13, head[0] + width * 0.13, head[1] + height * 0.12], 180, 360, fill=colors["hair"])
    draw.rounded_rectangle([head[0] - width * 0.12, head[1] - height * 0.02, head[0] + width * 0.12, head[1] + height * 0.17], radius=int(width * 0.055), fill=colors["hair"])
    draw.ellipse([head[0] - width * 0.03 + yaw * width * 0.05, head[1] + height * 0.10, head[0] + width * 0.05 + yaw * width * 0.05, head[1] + height * 0.22], fill=colors["hair"])
    draw.line([(center_x + shift - shoulder_w / 2, torso_top + height * 0.02), (center_x + shift - hip_w / 2, torso_bottom)], fill=(255, 255, 255, 55), width=max(1, int(width * 0.012)))

    if lean:
        image = image.rotate(lean, resample=Image.Resampling.BICUBIC, center=(center_x, foot_y), fillcolor=(0, 0, 0, 0))
    return image


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    professional = [asset for asset in data["assets"] if asset.get("category") == "player" and asset.get("visualStyle") == "professional" and not asset.get("view")]
    existing_ids = {asset["id"] for asset in data["assets"]}
    generated: list[dict] = []
    for asset in professional:
        asset["view"] = "Front"
        asset["characterView"] = "Front"
        asset["availableCharacterViews"] = ["Front", "3/4 Back Left", "3/4 Back Right", "Back"]
        pose_id = asset.get("poseId") or key(asset.get("pose"))
        base_dir = STATIC / "assets" / "characters" / "professional" / asset["characterId"] / team_dir(asset["team"]) / "views" / pose_id
        master_dir = base_dir / "masters"
        thumb_dir = STATIC / "assets" / "character_thumbnails" / "professional" / asset["characterId"] / team_dir(asset["team"]) / "views" / pose_id
        for directory in (base_dir, master_dir, thumb_dir):
            directory.mkdir(parents=True, exist_ok=True)
        for view, slug in BACKSIDE_VIEWS:
            new_id = f"{asset['id']}_{slug}"
            asset_rel = f"/static/assets/characters/professional/{asset['characterId']}/{team_dir(asset['team'])}/views/{pose_id}/{slug}.webp"
            master_rel = f"/static/assets/characters/professional/{asset['characterId']}/{team_dir(asset['team'])}/views/{pose_id}/masters/{slug}.webp"
            thumb_rel = f"/static/assets/character_thumbnails/professional/{asset['characterId']}/{team_dir(asset['team'])}/views/{pose_id}/{slug}.webp"
            if new_id in existing_ids:
                continue
            master = draw_backside(asset, view, (720, 900))
            runtime_height = min(480, max(240, int(asset["defaultHeight"] * 3.1)))
            runtime_width = max(120, int(asset["defaultWidth"] * runtime_height / max(1, asset["defaultHeight"])))
            runtime = draw_backside(asset, view, (runtime_width, runtime_height))
            thumbnail = runtime.copy()
            thumbnail.thumbnail((140, 150), Image.Resampling.LANCZOS)
            master.save(STATIC / master_rel.removeprefix("/static/"), "WEBP", lossless=True, quality=96)
            runtime.save(STATIC / asset_rel.removeprefix("/static/"), "WEBP", lossless=True, quality=96)
            thumbnail.save(STATIC / thumb_rel.removeprefix("/static/"), "WEBP", lossless=True, quality=96)
            record = deepcopy(asset)
            record.update({"id": new_id, "view": view, "characterView": view, "asset": asset_rel, "master": master_rel, "thumbnail": thumb_rel, "supportsMirror": False, "facingSupport": []})
            generated.append(record)
            existing_ids.add(new_id)

    data["assets"].extend(generated)
    data["schemaVersion"] = max(int(data.get("schemaVersion", 0)), 7)
    data["professionalCharacterViews"] = ALL_VIEWS
    data["defaultCharacterView"] = "Front"
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"base professional={len(professional)} generated_backside={len(generated)} total_assets={len(data['assets'])}")


if __name__ == "__main__":
    main()
