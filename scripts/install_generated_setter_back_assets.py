from __future__ import annotations

import json
import re
from copy import deepcopy
from collections import deque
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"
GENERATED_ROOT = Path("C:/Users/LL/.codex/generated_images/019f8a92-f704-7731-af72-272674a7006a")

CHARACTER_ID = "female_athlete_01"
ROLE = "setter"
VIEW = "Back"
POSES = {
    "Ready": "call_oIAowQuHf1Khz1er3yesAgu0.png",
    "Front Set": "call_Qz7tXNskPke7ZWmaT6aS4VC7.png",
    "Back Set": "call_oG9iZhp8pffr9kyLyYIZUr3T.png",
    "Jump Set": "call_XrUgx6vdGshxlYtAMAsLteuj.png",
    "One-Hand Set": "call_BljiFabFa5pGksaMaFZdBfyH.png",
    "Setter Dump": "call_khQ8oBOdPsZRuNysqGOoAKfu.png",
    "Transition": "call_PMScFzauz09n5vmh7kcs8X7D.png",
    "Defensive Ready": "call_Sq8D4Uqt1nRXDBK2q20QOiRT.png",
    "Emergency Set": "call_gKVmGmQoFHJjmajQ3WAGhnNL.png",
}
TEAMS = {
    "A": {
        "prefix": "professional",
        "uniform": "forest_green_gold_team_a",
        "asset_dir": "team_a",
        "thumb_dir": "team_a",
    },
    "B": {
        "prefix": "professional_team_b",
        "uniform": "navy_cyan_team_b",
        "asset_dir": "team_b",
        "thumb_dir": "team_b",
    },
}


def key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def remove_magenta(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size

    def backgroundish(x: int, y: int) -> bool:
        red, green, blue, alpha = pixels[x, y]
        if alpha == 0:
            return True
        magenta = red > 120 and blue > 120 and green < 175 and abs(red - blue) < 105
        saturated_purple = red > 145 and blue > 105 and green < 135
        hot_pink_edge = red > 185 and blue > 150 and green < 170
        return magenta or saturated_purple or hot_pink_edge

    queue: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))
    while queue:
        x, y = queue.popleft()
        if (x, y) in seen or not 0 <= x < width or not 0 <= y < height:
            continue
        seen.add((x, y))
        if not backgroundish(x, y):
            continue
        red, green, blue, alpha = pixels[x, y]
        pixels[x, y] = (red, green, blue, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if 0 < alpha < 220:
                pixels[x, y] = (red, green, blue, 0)
                continue
            if alpha and (red > 180 and blue > 135 and green < 170):
                pixels[x, y] = (red, green, blue, 0)
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else image


def recolor_team_b(image: Image.Image) -> Image.Image:
    recolored = image.copy()
    pixels = recolored.load()
    for y in range(recolored.height):
        for x in range(recolored.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            if green > red * 1.05 and green > blue * 1.05 and green > 45:
                luminance = 0.299 * red + 0.587 * green + 0.114 * blue
                shade = max(0.35, min(1.25, luminance / 95))
                pixels[x, y] = (
                    int(15 * shade),
                    int(57 * shade),
                    int(96 * shade),
                    alpha,
                )
            elif red > 145 and green > 95 and blue < 70:
                luminance = 0.299 * red + 0.587 * green + 0.114 * blue
                shade = max(0.55, min(1.35, luminance / 150))
                pixels[x, y] = (
                    int(63 * shade),
                    int(177 * shade),
                    int(205 * shade),
                    alpha,
                )
    return recolored


def remove_runtime_chroma(image: Image.Image) -> Image.Image:
    cleaned = image.convert("RGBA")
    pixels = cleaned.load()
    for y in range(cleaned.height):
        for x in range(cleaned.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 0 and red > 180 and blue > 140 and green < 100:
                pixels[x, y] = (red, green, blue, 0)
    return cleaned


def save_versions(image: Image.Image, *, team: str, pose: str) -> tuple[str, str, str, int, int]:
    pose_key = key(pose)
    team_meta = TEAMS[team]
    base = f"/static/assets/characters/professional/{CHARACTER_ID}/{team_meta['asset_dir']}/views/back"
    thumbs = f"/static/assets/character_thumbnails/professional/{CHARACTER_ID}/{team_meta['thumb_dir']}/views/back"
    master_rel = f"{base}/masters/{pose_key}.png"
    runtime_rel = f"{base}/{pose_key}.webp"
    thumb_rel = f"{thumbs}/{pose_key}.webp"
    for rel in (master_rel, runtime_rel, thumb_rel):
        (STATIC / rel.removeprefix("/static/")).parent.mkdir(parents=True, exist_ok=True)
    image = remove_runtime_chroma(image)
    image.save(STATIC / master_rel.removeprefix("/static/"), "PNG")
    runtime = image.copy()
    runtime.thumbnail((416, 480), Image.Resampling.LANCZOS)
    runtime = remove_runtime_chroma(runtime)
    runtime.save(STATIC / runtime_rel.removeprefix("/static/"), "WEBP", lossless=True, quality=98)
    thumb = image.copy()
    thumb.thumbnail((140, 150), Image.Resampling.LANCZOS)
    thumb = remove_runtime_chroma(thumb)
    thumb.save(STATIC / thumb_rel.removeprefix("/static/"), "WEBP", lossless=True, quality=96)
    return master_rel, runtime_rel, thumb_rel, runtime.width, runtime.height


def manifest_id(team: str, pose: str) -> str:
    return f"{TEAMS[team]['prefix']}_{CHARACTER_ID}_{key(pose)}_back"


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = data["assets"]
    by_id = {asset["id"]: asset for asset in assets}
    template = next(asset for asset in assets if asset["id"] == "professional_female_athlete_01_ready")
    installed = []
    for pose, filename in POSES.items():
        source = GENERATED_ROOT / filename
        if not source.is_file():
            raise FileNotFoundError(source)
        team_a_image = remove_magenta(source)
        for team in ("A", "B"):
            image = team_a_image if team == "A" else recolor_team_b(team_a_image)
            master, runtime, thumb, width, height = save_versions(image, team=team, pose=pose)
            asset_id = manifest_id(team, pose)
            asset = by_id.get(asset_id)
            if asset is None:
                asset = deepcopy(template)
                asset["id"] = asset_id
                assets.append(asset)
                by_id[asset_id] = asset
            asset.update(
                {
                    "category": "player",
                    "objectKind": "character",
                    "characterId": CHARACTER_ID,
                    "visualStyle": "professional",
                    "approvalStatus": "approved",
                    "role": ROLE,
                    "pose": pose,
                    "poseId": key(pose),
                    "team": team,
                    "uniform": TEAMS[team]["uniform"],
                    "asset": runtime,
                    "master": master,
                    "thumbnail": thumb,
                    "defaultWidth": max(74, round(width / max(1, height) * (164 if pose in {"Ready", "Defensive Ready"} else 190))),
                    "defaultHeight": 164 if pose in {"Ready", "Defensive Ready"} else 190,
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
                    "releaseStatus": "released",
                    "visibleInEditor": True,
                    "professionalGrade": True,
                    "containsNet": False,
                    "containsCourt": False,
                    "sourceQualityReference": "professional_team_a_middle_jump_block_back",
                }
            )
            installed.append(asset_id)
    data["schemaVersion"] = max(int(data.get("schemaVersion", 0)), 8)
    notes = data.setdefault("heroPack", {}).setdefault("notes", [])
    if "Setter Back View Pack" not in notes:
        notes.append("Setter Back View Pack")
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"installed={len(installed)}")
    print("\n".join(installed))


if __name__ == "__main__":
    main()
