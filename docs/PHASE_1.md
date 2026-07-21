# Phase 1 scope and status

## Completed

- Independent FastAPI application and private data directories
- Full 18 × 9 indoor court with free space, two halves, zones 1-6, attack lines, net, grid, and antennas
- Original native-SVG player figures, two team styles, roles, and complete initial pose lists
- Coaches, balls, targets, carts, blocking aids, and training equipment
- Movement and ball arrows, shapes, highlighted areas, and text
- Move, multi-select, resize, rotate, mirror, duplicate, delete, lock, layer ordering, zoom, and pan
- Undo/redo, clipboard shortcuts, and keyboard movement
- Independent multi-frame drills with add, duplicate, delete, rename, and reorder actions
- Full drill-information form
- Versioned persistent JSON drill and practice storage
- Searchable Drill Library and basic ordered Practice Builder
- PNG download and print layout
- Automated validation and isolated persistence tests

## Deliberately deferred

- Drag-selection rectangle and editable freehand control points
- Generated thumbnail images in Library cards
- Drag-and-drop frame and practice ordering
- Server-generated PDF, PowerPoint, GIF, video, and share links
- Collaboration, authentication, and cloud synchronization
- Optional file/API integration packages for Volleyball Scout

Deferred exports are not presented as working buttons.

## Phase 2 recommendations

1. Add a dedicated path editor with editable Bézier and freehand points.
2. Add drag-box selection and grouped transforms.
3. Generate and persist actual frame thumbnails.
4. Add drag-and-drop ordering with keyboard-accessible alternatives.
5. Add JSON drill-package import/export and schema migrations.
6. Add PDF and PowerPoint exporters behind explicit capability checks.
7. Add end-to-end browser tests and automated visual regression snapshots.
8. Package the local app as a signed Windows desktop launcher.
