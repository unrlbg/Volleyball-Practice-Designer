# Professional Hero Pack

The Hero Pack is the approved visual-identity baseline for Volleyball Practice
Designer. The editor exposes only Professional player assets.

## Recurring identities

- `female_athlete_01` — Setter
- `female_athlete_02` — Outside Hitter
- `female_athlete_03` — Middle Blocker
- `female_athlete_04` — Libero
- `female_athlete_05` — Opposite
- `coach_01` — Coach

Each role keeps one face, hairstyle, body type, uniform construction, footwear,
lighting direction and premium semi-realistic rendering language across its
poses. The Opposite is a separate, taller and more power-oriented athlete; it
does not reuse the Outside identity.

Team A uses green/yellow. Team B uses dark-blue/light-blue recolors of the same
identity and pose masters. Team changes never replace the athlete. The Libero
keeps its contrasting burnt-orange/cream uniform.

## Approved attacking sequences

Outside Hitter and Opposite each include:

- Attack Start
- Approach Step 1
- Approach Step 2
- Takeoff
- Jump Attack
- High Contact
- Line Attack
- Cross-Court Attack
- Tip
- Roll Shot
- Back-Row Attack
- Landing
- Transition After Attack

Middle Blocker includes:

- Quick Attack Ready
- First-Tempo Approach
- Takeoff
- Front Quick Attack
- Behind Setter Quick
- One-Foot Slide Approach
- One-Foot Slide Takeoff
- Slide Attack Contact
- Gap Attack
- Push Attack
- Landing
- Transition After Attack

These attacking actions are bespoke approved masters, not labels mapped to
another role or unrelated pose. Legacy Middle labels such as Quick Attack,
Quick Approach, Slide Approach and Slide Attack remain as Professional aliases
for safe drill compatibility.

## Pose groups

The editor groups valid manifest-backed poses by role:

- Outside: Ready, Reception, Attack, Block, Defense, Transition
- Opposite: Attack, Transition; empty categories stay hidden until artwork is
  approved
- Middle: Ready, Quick Attack, Slide Attack, Block, Transition

The thumbnail and placed player resolve the same exact manifest asset ID.

## Anchors and size

Grounded approach, ready, landing and transition poses use a feet anchor.
Airborne poses use a body-center anchor plus a landing reference. One-foot
slide takeoff/contact poses use the takeoff foot as their editor anchor.
Airborne assets use a slightly taller default box while preserving a tight
selection area.

Horizontal mirroring and left/right facing are supported. Vertical flipping is
hidden for player characters because it is not a valid volleyball action.

## Offline tiers

Every approved pose is stored locally as:

1. a high-resolution master under
   `app/static/assets/characters/professional/<characterId>/<team>/masters/`;
2. a runtime WebP under
   `app/static/assets/characters/professional/<characterId>/<team>/`;
3. a thumbnail WebP under
   `app/static/assets/character_thumbnails/professional/<characterId>/<team>/`.

All tiers use real alpha transparency and work without network access.

## Professional-only boundary and migration

Professional assets require `approvalStatus: "approved"`. Legacy Vector assets
are never selectable or rendered in the normal editor. Generic Player remains
hidden.

Old player objects migrate to Professional character objects on load. Exact
available attacking poses are retained. Position, size, rotation, facing,
mirror, opacity, assigned court, layer, lock state and frame membership are
preserved.

## Expansion rule

Future poses must begin from the matching recurring identity and pass in-editor
review at reduced scale, left/right facing, mirrored, rotated, duplicated,
saved/reloaded, exported and printed. No new pose is exposed until both Team A
and Team B manifest records and local image tiers validate at startup.
