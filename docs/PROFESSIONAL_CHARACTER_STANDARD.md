# Professional Character Standard

The Professional Character Library has one accepted quality level: Professional.

No player or coach figure may appear in the Court Editor, Asset Library, PNG export, PowerPoint export, saved drills, or reloaded drills unless it matches the official reference-image benchmark for anatomy, rendering, lighting, shadows, proportions, uniform detail, realism, and readability.

## Rejected Asset Types

Do not expose:

- stick figures
- flat vector people
- simplified drawings
- mirrored front views
- placeholders
- unfinished artwork
- mixed-quality Professional candidates

Unfinished or rejected assets may remain in the manifest only as hidden audit records. They must use `visibleInEditor: false` and a hidden `releaseStatus`, such as `hidden_quality_hold`, and must not be returned through app-visible asset APIs.

## Official Camera Views

The long-term official view set is:

- Front
- 15° Back
- 30° Back
- 45° Back
- 60° Back
- 75° Back
- 90° Back (Straight Back)

The first active production priority is only `45° Back`. Do not begin exposing the other back-angle views until their artwork, metadata, exports, save/reload behavior, and browser verification are complete.

## 45° Back Defensive Library

The `45° Back` angle is the primary defensive coaching view. Defensive figures should be built in this angle first for:

- Setter
- Outside
- Opposite
- Middle
- Libero
- Coach

Required defensive poses:

- Defense Ready
- Defensive Shuffle
- Split Step
- Low Defensive Position
- Left Defensive Position
- Right Defensive Position
- Deep Defense
- Mid Defense
- Short Defense
- Line Defense
- Cross-Court Defense
- Cover Behind Block
- Pipe Defense
- Transition Defense
- Forearm Dig
- One Knee Dig
- Side Lunge Dig
- Split Dig
- Emergency Dig
- Forward Dive
- Side Dive
- Pancake
- Sprawl Defense
- Roll Recovery
- Get Up
- Ready Again

## Consistency Requirements

Every released figure in a role library must use the same recurring athlete and preserve hairstyle, face, body proportions, uniform, shoes, knee pads, rendering, shadows, and lighting. Only body mechanics, defensive posture, and camera angle may change.

Every pose must also be technically correct for volleyball. For example, defense ready requires hips back, chest forward, bent knees, and balanced weight; forearm dig requires a realistic platform; pancake requires correct hand position.

## Release Gate

Before a figure becomes visible:

- artwork is complete and matches the official benchmark
- asset, master, and thumbnail paths exist
- metadata uses exact manifest values for role, pose, team, category, view, and visual style
- no hidden release status remains
- the figure works in Court Editor, Asset Library, PNG export, PowerPoint export, frame duplication, court duplication, save, and reload
- browser verification confirms cards and thumbnails render

If any item fails the gate, skip only that asset. Never hide or break the entire library.
