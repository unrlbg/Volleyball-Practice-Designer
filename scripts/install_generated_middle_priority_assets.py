from __future__ import annotations

import math
from pathlib import Path

from PIL import Image


GENERATED_ROOT = Path("C:/Users/LL/.codex/generated_images/019f8a92-f704-7731-af72-272674a7006a")
ITEMS = {
    "jump_block": GENERATED_ROOT / "call_Uq1AheJ3J9MAvOqtw884xDMd.png",
    "jump_block_left": GENERATED_ROOT / "call_giqNn8z4DjvP5LsDUZgFpN4V.png",
    "jump_block_right": GENERATED_ROOT / "call_2VZsRVPW5TmEfKQ0JsuLVHnl.png",
    "jump_block_spread": GENERATED_ROOT / "call_YthBrHYqeUiXaO7Scv2eCSip.png",
    "jump_block_close": GENERATED_ROOT / "call_CjsvAtuMYBPvvGdOfWqEQGkt.png",
    "quick_block": GENERATED_ROOT / "call_vqE5i6rtVVQqUEruxhpq6HLN.png",
}

BASE = Path("app/static/assets/characters/professional/team_a/middle_blocker/back")
THUMBS = Path("app/static/assets/character_thumbnails/professional/team_a/middle_blocker/back")


def remove_magenta(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            distance = math.sqrt((red - 255) ** 2 + green**2 + (blue - 255) ** 2)
            if distance < 92 and red > 185 and blue > 185 and green < 130:
                pixels[x, y] = (red, green, blue, 0)
            elif red > 170 and blue > 170 and green < 145:
                edge_alpha = max(0, min(255, int((distance - 62) * 4)))
                pixels[x, y] = (red, green, blue, min(alpha, edge_alpha))
    bbox = image.getbbox()
    image = image.crop(bbox) if bbox else image
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha and red > 150 and blue > 150 and green < 130:
                pixels[x, y] = (min(red, 132), max(green, 80), min(blue, 132), alpha)
    return image


def main() -> None:
    for slug, source in ITEMS.items():
        image = remove_magenta(source)
        master = BASE / "masters" / f"{slug}.png"
        runtime = BASE / f"{slug}.webp"
        thumbnail = THUMBS / f"{slug}.webp"
        master.parent.mkdir(parents=True, exist_ok=True)
        thumbnail.parent.mkdir(parents=True, exist_ok=True)
        image.save(master, "PNG")
        runtime_image = image.copy()
        runtime_image.thumbnail((416, 480), Image.Resampling.LANCZOS)
        runtime_image.save(runtime, "WEBP", lossless=True, quality=98)
        thumb_image = image.copy()
        thumb_image.thumbnail((140, 150), Image.Resampling.LANCZOS)
        thumb_image.save(thumbnail, "WEBP", lossless=True, quality=96)
        print(slug, image.size, runtime_image.size, thumb_image.size)


if __name__ == "__main__":
    main()
