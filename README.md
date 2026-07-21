# Volleyball Practice Designer

An independent, desktop-oriented local web application for building volleyball drills visually and organizing them into complete practices.

This repository is standalone. It does not read from, write to, import, or depend on Volleyball Scout.

## Phase 1 features

- Large pan/zoom SVG workspace containing one, two, or three independently editable courts
- Selectable courts with move, aspect-locked resize, rotation, rename, lock, copy/paste, delete, and court-layer ordering
- Single, two-horizontal, two-vertical, three-horizontal, three 2+1, and Skill Stations templates
- Independent attack lines, zone labels, grid, antennas, net, style, name, position, and lock state per court
- Court assignment for players, balls, equipment, arrows, shapes, and text
- Court-only duplication and deep court-with-contents duplication
- 130 bundled, offline SVG files: 107 player poses, 3 blue/yellow ball assets, 19 equipment assets, and 1 safe fallback
- Consistent Team A green/yellow and Team B dark-blue/light uniforms, distinct liberos, and a neutral coach
- Setter, Libero, Middle, Outside, Opposite, Generic Player, and Coach roles with role-specific pose libraries
- Four true ball-cart variants plus cones, targets, blocking equipment, and training equipment
- Searchable/filterable Asset Library review screen and manifest-driven palette thumbnails
- Three experimental semi-realistic directions with 36 review assets, direct comparison, preference setting, and Legacy Vector fallback
- Straight, curved, dashed, double-ended, movement, and trajectory arrows
- Shapes, responsibility areas, target circles, and text
- Selection, multi-selection, moving, resize, rotation, mirror, lock, duplicate, delete, and layer order
- Keyboard copy/paste, duplicate, undo/redo, delete, escape, and arrow-key movement
- Multiple independent drill frames with add, duplicate, delete, rename, and reorder
- Drill information form and persistent JSON storage
- Searchable Drill Library
- Basic practice builder using saved drills
- Selected-court, all-courts, current-viewport, and full-workspace PNG export
- One-court-per-page, all-courts landscape, and multi-page print preparation
- FastAPI test suite

## Technical stack

- Python 3.11+
- FastAPI and Uvicorn
- Native HTML, CSS, and JavaScript (no frontend build step)
- Native SVG editor
- Versioned JSON documents on disk
- Pytest and FastAPI TestClient

### Why native SVG

Fabric.js and Konva.js both provide mature transform controls and PNG export. Konva has especially strong scene/layer performance; Fabric offers a convenient serialized canvas. This first phase uses native SVG because the product depends on clean vector player figures, needs to run fully offline without a JavaScript package CDN, and benefits from DOM-level accessibility and printing. The saved format is a renderer-neutral object model, so a future renderer can be introduced without migrating drill semantics.

## Start on Windows

Exact manual setup and development start commands:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000`. Uvicorn uses port 8000 when no port is supplied.

For the packaged local launcher on port 8765:

From PowerShell:

```powershell
cd "C:\path\to\volleyball_practice_designer"
.\scripts\start.ps1
```

Or double-click:

```text
scripts\start.bat
```

The first start creates the project's private `.venv`, installs dependencies, starts the application, and opens:

```text
http://127.0.0.1:8765
```

Manual start:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m app.main
```

`scripts\start.bat` and `scripts\start.ps1` both create `.venv` when necessary, install the pinned dependencies, run the local launcher, and open the browser. The launcher URL is `http://127.0.0.1:8765`.

## Tests

```powershell
pytest -q
```

The tests use a repository-local temporary directory and never read or erase real saved drills or practices.

## Data and portability

Saved content lives in:

- `data/drills/<uuid>.json`
- `data/practices/<uuid>.json`
- `data/exports/`

Set `VPD_DATA_DIR` to use another data directory. Writes are atomic. Each document includes a schema version and timestamps.

Schema version 2 stores an ordered `courts` array in every frame. Each normal object may have a `courtId`; it remains independently editable, but follows its assigned court when that court moves or is duplicated with contents. Legacy schema-1 drills are migrated automatically to one centered selectable court.

The editor stores stable `assetId` values plus role, pose, team, facing, geometry, opacity, and layer order as plain JSON. Legacy objects without an `assetId` are resolved from their semantic fields when loaded. Unknown references use the bundled fallback instead of breaking a drill. It does not store SVG DOM or library-specific canvas state.

PNG exports are downloaded by the browser to the browser's configured Downloads folder. `data/exports/` is reserved for later server-generated export formats.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Runtime health |
| GET | `/api/assets` | Local visual asset manifest |
| GET/POST | `/api/drills` | List or create drills |
| GET/PUT/DELETE | `/api/drills/{id}` | Load, rename/update, or delete a drill |
| POST | `/api/drills/{id}/duplicate` | Deep-copy a saved drill |
| GET/POST | `/api/practices` | List or create practices |
| GET/PUT/DELETE | `/api/practices/{id}` | Load, update, or delete a practice |
| POST | `/api/practices/{id}/duplicate` | Deep-copy a practice |

Interactive API documentation is available at `/docs` while the server is running.

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+C`, `Ctrl+V` | Copy and paste |
| `Ctrl+D` | Duplicate |
| `Ctrl+Z`, `Ctrl+Y` | Undo and redo |
| `Delete` | Delete unlocked selection |
| `Escape` | Clear selection or drawing tool |
| Arrow keys | Move 1 unit |
| Shift + Arrow keys | Move 10 units |
| Shift + click | Add/remove from selection |

Shortcuts are ignored while typing in form controls.

## Known Phase 1 limitations

- Drag-box selection and freehand path point editing are not yet implemented.
- Frame reordering and renaming use a compact action prompt rather than drag-and-drop.
- Practice drills can be reordered with Up/Down controls; drag reordering is planned for the next iteration.
- Drill preview cards use a court schematic rather than generated frame thumbnails.
- Experimental artwork currently covers the 12-pose approval set per style; other role/pose combinations intentionally fall back to Legacy Vector.
- Newly added objects use the selected court or Court 1. Objects dragged across a boundary are not automatically reassigned.
- PNG export uses browser canvas; SVG-internal fonts use available system fonts.
- PDF, PowerPoint, animation, video, and sharing are intentionally not shown as finished exports.

## Future integration boundary

Any Volleyball Scout integration must be explicit and optional through a documented JSON package, image/PDF export, or API. No shared folders, databases, or internal code dependencies are permitted.

See `docs/USER_GUIDE.md`, `docs/DEVELOPMENT.md`, `docs/DATA_MODEL.md`, and `docs/PHASE_1.md` for the complete operating and implementation reference.
