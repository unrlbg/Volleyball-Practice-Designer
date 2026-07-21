# Phase 1 validation record

Validation date: 2026-07-20

## Automated checks

- Python compile check: passed
- JavaScript syntax check: passed
- Pytest: `58 passed in 2.37s`
- Test storage: repository-local temporary directories only

## Live browser verification

The FastAPI application was started against an isolated browser-test data directory and exercised in the Codex in-app browser.

Verified:

- Application root, static CSS/JS, and API requests loaded successfully
- The upgraded application loaded from its isolated validation server without new console warnings or errors
- Full 18 × 9 court, both halves, twelve zone labels, two attack lines, and net rendered
- Attack lines, zone labels, and net each hid and restored correctly
- The Asset Library reported 129 usable assets; equipment search returned exactly four cart variants
- Team A and Team B players could be added; role and pose thumbnails changed the selected asset
- Player facing changed through Mirror, and Reset size restored intended proportions
- Selected figures moved with drag, resized with the corner handle, rotated with the rotation handle, mirrored, duplicated, and deleted
- Twenty-five player/ball/cart SVG objects rendered simultaneously, remained interactive, and survived save/reload
- A movement arrow was drawn by dragging on the court
- Text was added and edited through the Properties panel
- A frame was duplicated and renamed; adding an object to the duplicate left the original object count unchanged
- Drill metadata was entered and saved
- After page reload, the saved drill appeared in Drill Library and reopened with two frames and the original object count
- The saved drill was added to a practice and the practice was saved
- PNG export completed and displayed `PNG exported with all visual assets`
- Print control invoked successfully and print-specific CSS was present

## Layout verification

- Wide desktop screenshot: 1920 × 1080 browser target; editor panels, toolbar, court, and frame strip remained aligned
- Compact desktop target: 1366 × 768; browser content viewport reported 1280 × 720 after browser chrome, with no horizontal document overflow
- Compact screenshot confirmed both side panels, the complete court, toolbar, and frame strip remained usable

## Notes

Browser tests used disposable data under `work/` and did not touch normal saved drills or practices. PNG download completion was confirmed through the application's success state; the in-app browser did not expose the browser download file path for a data-URL download.

The asset-specific suite also verifies 166 unique manifest IDs and files, every required Legacy Vector role/pose for both teams, distinct libero and coach styling metadata, four cart variants, three ball variants, transparent SVGs with no external references, API migration/fallback behavior, transform preservation, independent frame copies, and migration of 96 objects within the 0.25-second test budget.

## Multiple-court and player-style upgrade

- Three Courts 2+1 rendered as three independent selectable court groups
- Add, delete, court-only duplicate, and court-with-contents deep duplicate were exercised
- Deep duplication changed 3 courts/7 objects to 4 courts/14 objects; deleting the copied court returned to 3 courts while preserving unassigned contents
- Court locking produced the expected locked state
- Skill Stations produced one full court, one half-size court, and a free equipment zone
- Court geometry retained an exact 2:1 width/height ratio
- A saved three-court drill reopened with all court names, settings, assignments, and objects
- The stress frame contained 3 courts and 50 visual objects, duplicated into an independent second frame, saved, exported, and reopened
- Court-aware dragging moved the selected court and its assigned contents; empty-canvas dragging changed the viewport pan transform
- Selected-court and all-courts PNG export both reached their success state
- Asset Library displayed 165 selectable assets and a direct A/B/C setter comparison
- Semi-Realistic C selection resolved the setter to a local runtime WebP
- 1366×768 and 1920×1080 both reported no horizontal or vertical document overflow after the compact-layout adjustment
- Final browser console: zero errors or warnings

The expanded suite verifies old single-court migration, three-court persistence, names, positions, independent settings, assignment retention, aspect ratio, deep-copy ID independence, templates, export modes, 36 experimental review assets, and 54-object migration within the 0.25-second budget.
