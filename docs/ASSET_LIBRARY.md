# Visual asset library

## Inventory

The manifest contains 166 local assets:

- 130 Legacy Vector SVGs:
  - 107 players: 100 Team A/Team B role poses and 7 neutral coach poses
  - 3 blue/yellow competition-ball arrangements
  - 19 equipment items, including 4 real ball-cart variants
  - 1 neutral fallback
- 36 Experimental player review assets:
  - 12 poses for Semi-Realistic A
  - 12 poses for Semi-Realistic B
  - 12 poses for Semi-Realistic C

The in-app Asset Library displays 165 usable assets; the fallback remains hidden from normal selection.

Each experimental character has a transparent high-resolution PNG source, optimized transparent WebP runtime asset, compact transparent WebP thumbnail, and style/team/role/pose metadata. They are original generic athletes with no numbers, sponsors, clubs, federations, or identifiable real players.

## Organization

```text
app/static/assets/
  players/team_a/<role>/
  players/team_b/<role>/
  players/coach/coach/
  balls/
  equipment/ball_carts/
  equipment/blocking/
  equipment/targets/
  equipment/general/
  experimental/
    sources/
    style_a/{high,runtime,thumbs}/
    style_b/{high,runtime,thumbs}/
    style_c/{high,runtime,thumbs}/
  fallback.svg
  manifest.json
```

Every manifest entry has a stable `id`, local `asset` and `thumbnail` paths, `category`, `defaultWidth`, `defaultHeight`, and `anchor`. Player entries also identify `team`, `role`, and `pose`. Equipment entries identify `equipmentType` and `variant`. Experimental entries also identify `style`, `poseKey`, `source`, and `experimental`.

## Regeneration

Recreate the deterministic Legacy Vector set with:

```powershell
python scripts\generate_assets.py
```

After approved chroma-key contact sheets have been converted to alpha, rebuild experimental derivatives with:

```powershell
python scripts\build_experimental_assets.py
```

The image-generation prompts used three contact sheets with the same exact 12-cell pose order. The built-in image-generation path created the source sheets, and the bundled chroma-key helper removed the flat magenta background before the build script generated individual PNG/WebP files.

## Selection and fallback

Player Visual Style is stored locally as a user preference. Experimental poses resolve first when the selected style contains the requested team/role/pose. All missing combinations resolve to Legacy Vector without changing drill semantics.

Legacy objects that only contain semantic fields such as `team`, `role`, `pose`, or `label` are mapped to the nearest current manifest entry. Aliases cover capitalization and earlier cart/pose names. Existing transforms and layer order are retained. Records that cannot be mapped receive the safe fallback asset and remain editable.
