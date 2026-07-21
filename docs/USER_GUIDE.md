# User guide

## Start the application

Run `scripts\start.ps1` from PowerShell or double-click `scripts\start.bat`. Open `http://127.0.0.1:8765` if the browser does not open automatically.

## Build a drill

1. Open **Court Editor**.
2. Choose a layout under the court toolbar and select **Arrange Courts**, or use **Add Court**.
3. Click a court to select it. Drag it to move it, use the corner handle for aspect-locked resize, and use the Properties panel to rename, rotate, style, or lock it.
4. Choose Team A, Team B, or Neutral in the left panel.
5. Click a player, ball, or equipment thumbnail. It is assigned to the selected court, or Court 1.
6. Select an object to edit its Assigned court, team, role, pose/variant, facing, rotation, size, opacity, mirror, lock, and layer order.
7. Use **Reset size** to restore an asset's intended proportions. **Mirror** flips its facing direction.
8. Drag an unlocked object to move it. Use the corner handle to resize and the top handle to rotate.
9. Select an arrow tool, then drag from its start point to its end point.
10. Click Text label and enter the instruction.
11. Toggle attack lines, zone labels, grid, antennas, or net for the selected court.

## Multiple courts

Use **Duplicate Court Only** to copy the court geometry/settings. Use **Duplicate Court With Contents** to deep-copy all assigned players, balls, equipment, arrows, shapes, and text. Moving an assigned court moves its contents together.

**Fit All Courts** zooms and pans to the complete workspace. Drag empty canvas space to pan and use the mouse wheel or zoom buttons to zoom.

## Review visual assets

Open **Asset Library** to inspect all player poses, ball styles, equipment, and four cart variants. Search by role, pose, team, or equipment, then filter by category and team. These are the same local assets shown in the editor palette and exports.

The Player Visual Style review compares Semi-Realistic A, B, and C with the same setter front-set pose. Choosing a style updates available review poses; missing poses continue to use Legacy Vector.

## Frames

Use **Add frame** for an empty frame. The visible frame controls duplicate, delete, and move the current frame. Edit **Current frame name** and choose **Apply name** to rename it. A duplicate is independent from its source.

## Save and reopen

Open **Drill info**, provide a drill name, and apply the details. Select **Save drill**. Use **Drill Library** to search, open, duplicate, delete, or add the drill to a practice.

## Practice Builder

Choose **Add to practice** on a Library card. In My Practices, enter the practice details, adjust minutes, and use Up/Down to reorder drills. Select **Save practice**.

## Export and print

Choose a PNG mode before selecting **Export PNG**: Selected court, All courts, Current viewport, or Full workspace. The exporter waits for every local SVG/WebP asset and includes assigned objects outside court lines.

Print modes support one court per page, all courts on one landscape page, or multi-page courts.

## Shortcuts

- `Ctrl+C`, `Ctrl+V`: copy and paste
- `Ctrl+D`: duplicate
- `Ctrl+Z`, `Ctrl+Y`: undo and redo
- `Delete`: delete unlocked selection
- `Escape`: clear selection or cancel drawing
- Arrow keys: move one unit
- Shift + arrow keys: move ten units
- Shift + click: change multi-selection

Shortcuts do not run while a text input, textarea, or select is active.
