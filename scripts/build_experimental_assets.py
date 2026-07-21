"""Build experimental semi-realistic review assets from approved contact sheets.

The three source sheets are generated on a chroma-key background, converted to
alpha with the bundled image-generation helper, then split into independent
high-resolution PNG, runtime WebP, and thumbnail WebP files.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app" / "static" / "assets"
EXPERIMENTAL = ASSETS / "experimental"
MANIFEST = ASSETS / "manifest.json"

POSES = [
    ("setter_ready", "A", "setter", "Ready", "ready"),
    ("setter_front_set", "A", "setter", "Front Set", "front_set"),
    ("setter_back_set", "B", "setter", "Back Set", "back_set"),
    ("setter_jump_set", "B", "setter", "Jump Set", "jump_set"),
    ("outside_attack", "A", "outside", "Jump Attack", "jump_attack"),
    ("middle_block", "B", "middle", "Single Block", "single_block"),
    ("libero_reception", "A", "libero", "Reception", "reception"),
    ("libero_dig", "B", "libero", "Dig", "dig"),
    ("libero_dive", "A", "libero", "Dive", "dive"),
    ("coach_holding_ball", "Neutral", "coach", "Holding Ball", "holding_ball"),
    ("team_a_ready", "A", "generic", "Ready", "ready"),
    ("team_b_ready", "B", "generic", "Ready", "ready"),
]
STYLE_LABELS = {
    "style_a": "Semi-Realistic A",
    "style_b": "Semi-Realistic B",
    "style_c": "Semi-Realistic C",
}


def contain(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
    output = image.copy()
    output.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return output


def remove_alpha_dust(image: Image.Image, minimum_component: int = 60) -> Image.Image:
    """Remove isolated chroma-removal specks without touching real figure edges."""
    alpha = image.getchannel("A")
    pixels = alpha.load()
    width, height = alpha.size
    visited = bytearray(width * height)
    remove: list[tuple[int, int]] = []
    for y in range(height):
        for x in range(width):
            offset = y * width + x
            if visited[offset] or pixels[x, y] <= 18:
                visited[offset] = 1
                continue
            component = []
            stack = [(x, y)]
            visited[offset] = 1
            while stack:
                px, py = stack.pop()
                component.append((px, py))
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    if 0 <= nx < width and 0 <= ny < height:
                        neighbor = ny * width + nx
                        if not visited[neighbor] and pixels[nx, ny] > 18:
                            visited[neighbor] = 1
                            stack.append((nx, ny))
            if len(component) < minimum_component:
                remove.extend(component)
    if remove:
        cleaned = image.copy()
        cleaned_alpha = cleaned.getchannel("A")
        cleaned_pixels = cleaned_alpha.load()
        for x, y in remove:
            cleaned_pixels[x, y] = 0
        cleaned.putalpha(cleaned_alpha)
        return cleaned
    return image


def split_sheet(style: str) -> list[dict]:
    source = EXPERIMENTAL / "sources" / f"{style}_sheet_alpha.png"
    sheet = Image.open(source).convert("RGBA")
    high_dir = EXPERIMENTAL / style / "high"
    runtime_dir = EXPERIMENTAL / style / "runtime"
    thumb_dir = EXPERIMENTAL / style / "thumbs"
    for directory in (high_dir, runtime_dir, thumb_dir):
        directory.mkdir(parents=True, exist_ok=True)

    entries = []
    cell_width = sheet.width / 4
    cell_height = sheet.height / 3
    for index, (slug, team, role, pose, pose_key) in enumerate(POSES):
        column, row = index % 4, index // 4
        crop = sheet.crop(
            (
                round(column * cell_width),
                round(row * cell_height),
                round((column + 1) * cell_width),
                round((row + 1) * cell_height),
            )
        )
        crop = remove_alpha_dust(crop)
        alpha_box = crop.getchannel("A").getbbox()
        if not alpha_box:
            raise RuntimeError(f"No figure found in {style} cell {index + 1}")
        crop = crop.crop(alpha_box)
        padding = max(8, round(max(crop.size) * 0.035))
        high = Image.new("RGBA", (crop.width + padding * 2, crop.height + padding * 2))
        high.alpha_composite(crop, (padding, padding))

        high_path = high_dir / f"{slug}.png"
        runtime_path = runtime_dir / f"{slug}.webp"
        thumb_path = thumb_dir / f"{slug}.webp"
        high.save(high_path, optimize=True)
        contain(high, 420, 520).save(runtime_path, "WEBP", quality=88, method=6)
        contain(high, 160, 190).save(thumb_path, "WEBP", quality=80, method=6)

        runtime = Image.open(runtime_path)
        display_height = 140 if slug != "libero_dive" else 92
        display_width = round(display_height * runtime.width / runtime.height)
        entries.append(
            {
                "id": f"experimental_{style}_{slug}",
                "category": "experimental_player",
                "experimental": True,
                "style": style,
                "styleLabel": STYLE_LABELS[style],
                "team": team,
                "role": role,
                "pose": pose,
                "poseKey": pose_key,
                "asset": f"/static/assets/experimental/{style}/runtime/{slug}.webp",
                "thumbnail": f"/static/assets/experimental/{style}/thumbs/{slug}.webp",
                "source": f"/static/assets/experimental/{style}/high/{slug}.png",
                "defaultWidth": display_width,
                "defaultHeight": display_height,
                "anchor": {"x": 0.5, "y": 0.98},
            }
        )
    return entries


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["assets"] = [
        asset for asset in manifest["assets"] if asset.get("category") != "experimental_player"
    ]
    for style in STYLE_LABELS:
        manifest["assets"].extend(split_sheet(style))
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Built {len(POSES) * len(STYLE_LABELS)} experimental review assets")


if __name__ == "__main__":
    main()
