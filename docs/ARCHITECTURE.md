# Architecture

## Boundaries

The browser is a renderer and interaction client. FastAPI owns persistence. The saved JSON format is the durable product contract and contains no SVG DOM, Fabric.js, or Konva.js state.

```text
Browser UI / native SVG editor
            |
       JSON over HTTP
            |
 FastAPI + asset registry
      |             |
Versioned JSON   Local SVG manifest
```

## Main modules

- `app/main.py`: application factory, static delivery, and local launcher
- `app/api/routes.py`: drill and practice CRUD API
- `app/models/schemas.py`: Pydantic persistence contracts
- `app/services/storage.py`: safe item IDs and atomic JSON replacement
- `app/services/assets.py`: manifest indexing, legacy aliases, migration, and fallback resolution
- `app/services/assets.py`: also upgrades schema-1 single-court frames to schema-2 court objects
- `app/static/assets/manifest.json`: stable IDs, paths, dimensions, anchors, teams, roles, poses, and variants
- `app/static/js/app.js`: renderer-neutral editor state, SVG renderer, asset review screen, library, and practice builder
- `scripts/generate_assets.py`: deterministic generator for the original local SVG set
- `scripts/build_experimental_assets.py`: splits approved alpha contact sheets into PNG sources, WebP runtime images, WebP thumbnails, and manifest entries

## Renderer-neutral object model

Every frame owns an ordered `objects` list. A visual object includes:

```json
{
  "id": "uuid",
  "type": "player",
  "label": "Setter",
  "assetId": "team_a_setter_jump_set",
  "role": "Setter",
  "pose": "Jump Set",
  "team": "A",
  "courtId": "court-uuid",
  "facing": "right",
  "x": 540,
  "y": 320,
  "width": 70,
  "height": 90,
  "rotation": 0,
  "scale": 1,
  "opacity": 1,
  "color": "#176b62",
  "mirror": false,
  "locked": false
}
```

Array order is layer order. Frame duplication is a deep copy and assigns new object IDs.

Every frame also owns an ordered `courts` list. Courts are rendered beneath normal objects but use the same selection, drag, rotate, lock, and layer-control concepts. Court resize writes `width` and derives `height = width / 2`. Assigned objects remain independent; court movement applies the same delta to them.

## Asset loading and migration

The server loads the manifest once at startup and exposes it through `GET /api/assets`. The browser renders each player, ball, or equipment object as a local SVG image. Every object remains independently selectable and transformable because interaction geometry belongs to the editor object rather than the SVG file.

When a drill is listed, opened, saved, created, or duplicated, the registry resolves missing or obsolete references from `team`, `role`, `pose`, `label`, and known aliases. It preserves position, size, rotation, scale, opacity, facing, locking, and layer order. Unresolvable records receive `fallback`, keeping the document editable.

PNG export fetches every referenced local SVG, embeds it as a data URI, waits for the composed SVG image to load, and only then rasterizes the frame. No CDN or network resource is required.

## Security and reliability

- Item IDs accept only alphanumeric characters, hyphens, and underscores.
- Temporary files are atomically replaced after complete writes.
- The server binds to loopback by default.
- Text is escaped before entering generated SVG/HTML.

