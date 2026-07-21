# Data model

All durable drills are UTF-8 JSON and use `schema_version: 2`. The model is independent from SVG, Fabric.js, Konva.js, or any other renderer.

## Drill

```json
{
  "id": "UUID",
  "schema_version": 2,
  "metadata": {
    "name": "Required drill name",
    "objective": "First-ball side-out",
    "tags": ["Reception", "Setting"]
  },
  "created_at": "UTC ISO-8601 timestamp",
  "modified_at": "UTC ISO-8601 timestamp",
  "frames": [],
  "thumbnail": null
}
```

`metadata.name` is required, trimmed, and limited to 200 characters. Other drill-information fields are preserved as additional metadata.

## Frame

A frame has a unique `id`, a user-visible `name`, an ordered `courts` array, and an ordered `objects` array. Array order is the layer order from back to front.

```json
{
  "id": "frame-uuid",
  "name": "Frame 1",
  "courts": [{
    "id": "court-uuid",
    "type": "court",
    "name": "Main Court",
    "x": 600,
    "y": 390,
    "width": 780,
    "height": 390,
    "rotation": 0,
    "locked": false,
    "style": "competition",
    "kind": "court",
    "settings": {
      "showAttackLines": true,
      "showZoneLabels": true,
      "showNet": true,
      "showGrid": false,
      "showAntennas": true
    }
  }],
  "objects": []
}
```

Court width and height maintain the regulation 2:1 proportion. Duplicating a frame creates new frame, court, and object IDs and remaps every `courtId`. Subsequent edits do not share references with the source frame.

## Visual object

Common fields are `id`, `type`, `label`, `assetId`, `courtId`, `x`, `y`, `width`, `height`, `rotation`, `scale`, `opacity`, `color`, `mirror`, `facing`, and `locked`.

- Players add `team`, `role`, and `pose`. Their `x`/`y` placement uses the manifest foot anchor so a pose change does not make the player jump off its court position.
- Equipment uses `type: equipment` and a specific `label`; ball-cart and ball choices are separate stable assets.
- Arrows add `dx`, `dy`, `curved`, and `thickness`.
- Text adds `text`.
- Shapes use width, height, color, and opacity.

`assetId` is the stable renderer-independent visual reference. The manifest record contains `id`, `category`, `asset`, `thumbnail`, `defaultWidth`, `defaultHeight`, `anchor`, and category-specific values such as `team`, `role`, `pose`, `equipmentType`, or `variant`. Older objects without `assetId` remain valid and are upgraded during API reads/writes. Unknown values resolve to `fallback`.

Schema-1 frames with only a `court` settings dictionary migrate to a single Court 1 object. Existing objects are assigned to that court, visual assets are resolved, and transforms and layer order are preserved. The legacy top-level `court` dictionary remains as a compatibility projection of the first court.

## Practice

A practice stores its name, date, team, objective, notes, timestamps, and ordered sections. Section drill entries reference saved drills by `drill_id` and retain the display name and planned duration.

## Storage behavior

Documents are written to a temporary sibling file and atomically replaced. IDs are restricted to alphanumeric characters, hyphens, and underscores. Empty, malformed, non-object, or unreadable JSON files are ignored by listings and treated as unavailable on direct load rather than crashing the server.
