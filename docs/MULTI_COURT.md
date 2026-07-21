# Multiple-court workspace

## Court objects

Every frame owns an ordered list of selectable court objects. Courts support move, regulation 2:1 aspect-locked resize, rotation, rename, lock/unlock, delete, copy/paste, and forward/backward court-layer ordering.

The court settings panel applies to the selected court. When no court is selected, it applies to Court 1.

## Object assignment

Players, balls, equipment, arrows, shapes, and text retain normal independent geometry and may store a `courtId`. New objects are assigned to the selected court, or Court 1 when another object is selected.

Moving a court also moves all objects assigned to it. Changing an object's Assigned court property does not alter its current coordinates.

## Duplication

- **Duplicate Court Only** creates a new independent court with copied settings and a new ID.
- **Duplicate Court With Contents** also deep-copies every assigned object, offsets it by the court displacement, creates new IDs, and points the copies at the new court.

Deleting a court leaves its former contents as unassigned workspace objects so material outside court boundaries is not destroyed.

## Templates

- Single Court
- Two Courts Horizontal
- Two Courts Vertical
- Three Courts Horizontal
- Three Courts 2+1
- Skill Stations: one full court, one half-size training court, and one editable free equipment zone

Templates remain normal editable court objects after creation.

## Export and print

PNG modes are Selected court, All courts, Current viewport, and Full workspace. Selected/all bounds include assigned objects outside court lines, preventing clipping. Local SVG and WebP assets are embedded before canvas rasterization.

Print modes are One court per page, All courts landscape, and Multi-page courts. Print pages are built from independent workspace SVG clones.
