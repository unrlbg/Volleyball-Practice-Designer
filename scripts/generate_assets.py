"""Generate the original, offline SVG visual library and its manifest.

The output contains no third-party logos, photographs, or external references.
Every file has a transparent background and a tight viewBox.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app" / "static" / "assets"

ROLE_POSES = {
    "generic": ["Standing", "Ready", "Moving", "Jumping"],
    "setter": [
        "Ready",
        "Front Set",
        "Back Set",
        "Jump Set",
        "One-Hand Set",
        "Setter Dump",
        "Defensive Position",
        "Transition",
    ],
    "libero": [
        "Reception",
        "Defensive Ready",
        "Dig",
        "Dive",
        "Overhead Defense",
        "Emergency Set",
        "Cover",
        "Transition",
    ],
    "middle": [
        "Ready",
        "Quick Approach",
        "Quick Attack",
        "Slide Approach",
        "Slide Attack",
        "Block Ready",
        "Single Block",
        "Moving Block",
        "Transition",
    ],
    "outside": [
        "Ready",
        "Reception",
        "Attack Start",
        "Approach",
        "Jump Attack",
        "Tip",
        "Roll Shot",
        "Block",
        "Defense",
        "Cover",
        "Transition",
    ],
    "opposite": [
        "Ready",
        "Attack Start",
        "Approach",
        "Jump Attack",
        "Tip",
        "Roll Shot",
        "Block",
        "Defense",
        "Cover",
        "Transition",
    ],
    "coach": [
        "Standing",
        "Holding Ball",
        "Tossing Ball",
        "Serving",
        "Attacking",
        "Giving Instructions",
        "Observing",
    ],
}

TEAM_STYLE = {
    "A": {"jersey": "#174f45", "jersey2": "#0c302b", "accent": "#f0c84b", "shorts": "#102f2c", "marker": "#f0c84b"},
    "B": {"jersey": "#173e68", "jersey2": "#0d2747", "accent": "#8fd8f2", "shorts": "#0e2948", "marker": "#8fd8f2"},
    "N": {"jersey": "#4d555b", "jersey2": "#272e33", "accent": "#d7dadc", "shorts": "#2f363b", "marker": "#c4c9cc"},
}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def pose_geometry(pose: str) -> dict[str, tuple[float, float]]:
    p = pose.lower()
    g = {
        "head": (60, 34),
        "neck": (60, 52),
        "ls": (47, 63),
        "rs": (73, 63),
        "le": (38, 92),
        "re": (82, 92),
        "lh": (34, 120),
        "rh": (86, 120),
        "hip": (60, 124),
        "lk": (48, 160),
        "rk": (72, 160),
        "lf": (42, 205),
        "rf": (80, 205),
    }
    if any(x in p for x in ("set", "overhead")):
        g.update(le=(43, 48), re=(77, 48), lh=(49, 26), rh=(71, 26))
    if "one-hand" in p:
        g.update(le=(42, 48), lh=(49, 27), re=(88, 86), rh=(98, 72))
    if any(x in p for x in ("block", "jump set")):
        g.update(le=(42, 37), re=(78, 37), lh=(43, 7), rh=(77, 7), hip=(60, 119), lk=(48, 157), rk=(72, 154), lf=(43, 194), rf=(79, 191))
    if any(x in p for x in ("attack", "serving", "dump", "tip", "roll shot", "tossing")):
        g.update(le=(36, 86), lh=(24, 105), re=(77, 38), rh=(83, 7), hip=(60, 119), lk=(43, 156), rk=(79, 151), lf=(34, 193), rf=(92, 188))
    if any(x in p for x in ("ready", "reception", "dig", "defense", "cover")):
        g.update(head=(60, 49), neck=(60, 66), ls=(46, 78), rs=(74, 78), le=(45, 104), re=(75, 104), lh=(56, 124), rh=(64, 124), hip=(60, 137), lk=(42, 164), rk=(80, 164), lf=(31, 204), rf=(91, 204))
    if any(x in p for x in ("approach", "moving", "transition", "slide")):
        g.update(head=(62, 39), neck=(60, 57), ls=(46, 68), rs=(73, 65), le=(30, 84), re=(87, 91), lh=(19, 70), rh=(97, 108), hip=(59, 128), lk=(38, 158), rk=(82, 151), lf=(24, 201), rf=(100, 183))
    if "dive" in p:
        g.update(head=(92, 89), neck=(78, 96), ls=(69, 87), rs=(72, 104), le=(44, 88), re=(45, 110), lh=(17, 84), rh=(18, 113), hip=(66, 127), lk=(48, 153), rk=(82, 153), lf=(27, 181), rf=(105, 178))
    if "rear" in p or "back set" in p:
        g["rear"] = (1, 1)
    return g


def limb(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], skin: str, width: int = 11) -> str:
    points = f"M{a[0]} {a[1]} Q{b[0]} {b[1]} {c[0]} {c[1]}"
    return (
        f'<path d="{points}" fill="none" stroke="#182321" stroke-width="{width + 4}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="{points}" fill="none" stroke="{skin}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def player_svg(role: str, pose: str, team: str) -> str:
    g = pose_geometry(pose)
    style = TEAM_STYLE[team]
    skin = "#c98962" if team == "A" else "#d39b76"
    if role == "coach":
        skin = "#c88d68"
    jersey, jersey2, accent, shorts, marker = style["jersey"], style["jersey2"], style["accent"], style["shorts"], style["marker"]
    if role == "libero":
        if team == "A":
            jersey, jersey2, accent = "#e8bd3f", "#b87a20", "#174f45"
        else:
            jersey, jersey2, accent = "#edf4f5", "#b8cbd0", "#173e68"
    rear = "rear" in g
    head_x, head_y = g["head"]
    torso = f"M{g['ls'][0]} {g['ls'][1]} Q60 56 {g['rs'][0]} {g['rs'][1]} L72 122 Q60 132 48 122Z"
    if "dive" in pose.lower():
        torso = "M68 86 Q80 93 78 105 L67 135 Q55 136 48 125 L57 95Z"
    ball = ""
    if any(word in pose.lower() for word in ("holding ball", "tossing ball")):
        bx, by = (30, 109) if "holding" in pose.lower() else (27, 55)
        ball = ball_svg_fragment(bx, by, 12)
    base = f'<ellipse cx="60" cy="207" rx="28" ry="7" fill="{marker}" opacity=".34"/><path d="M35 207 Q60 218 85 207" fill="none" stroke="{marker}" stroke-width="4" opacity=".8"/>'
    jersey_detail = (
        f'<path d="M49 78 Q60 83 71 78" fill="none" stroke="{accent}" stroke-width="5"/>'
        f'<path d="M52 101 L68 101" stroke="{accent}" stroke-width="4" opacity=".75"/>'
    )
    if rear:
        jersey_detail = f'<path d="M48 82 Q60 75 72 82" fill="none" stroke="{accent}" stroke-width="5"/>'
    arms = limb(g["ls"], g["le"], g["lh"], skin) + limb(g["rs"], g["re"], g["rh"], skin)
    legs = limb(g["hip"], g["lk"], g["lf"], skin, 13) + limb(g["hip"], g["rk"], g["rf"], skin, 13)
    shoes = (
        f'<ellipse cx="{g["lf"][0]}" cy="{g["lf"][1]}" rx="10" ry="5" fill="#f7f8f5" stroke="#26302e" stroke-width="2"/>'
        f'<ellipse cx="{g["rf"][0]}" cy="{g["rf"][1]}" rx="10" ry="5" fill="#f7f8f5" stroke="#26302e" stroke-width="2"/>'
    )
    hair = f'<path d="M{head_x-10} {head_y-5} Q{head_x} {head_y-18} {head_x+11} {head_y-4} Q{head_x+7} {head_y-10} {head_x-10} {head_y-5}Z" fill="#32231d"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 220" role="img" aria-label="{team} {role} {pose}">
<defs>
  <linearGradient id="jersey" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{jersey}"/><stop offset="1" stop-color="{jersey2}"/></linearGradient>
  <radialGradient id="skin"><stop stop-color="#e6b08b"/><stop offset="1" stop-color="{skin}"/></radialGradient>
  <filter id="soft"><feDropShadow dx="0" dy="2" stdDeviation="1.5" flood-opacity=".2"/></filter>
</defs>
<g filter="url(#soft)">{base}{legs}<path d="{torso}" fill="url(#jersey)" stroke="#182321" stroke-width="3"/>{jersey_detail}
<path d="M48 120 Q60 129 72 120 L75 140 Q60 148 45 140Z" fill="{shorts}" stroke="#182321" stroke-width="3"/>
{arms}<circle cx="{head_x}" cy="{head_y}" r="14" fill="url(#skin)" stroke="#182321" stroke-width="3"/>{hair}
<path d="M{head_x-5} {head_y+5} Q{head_x} {head_y+8} {head_x+5} {head_y+5}" fill="none" stroke="#8b5540" stroke-width="1.6" opacity=".7"/>
{shoes}{ball}</g></svg>'''


def ball_svg_fragment(x: float, y: float, radius: float) -> str:
    return f'''<g transform="translate({x} {y}) scale({radius / 24})">
<circle r="24" fill="#f1ca34" stroke="#17314e" stroke-width="2.5"/>
<path d="M-22-7 Q-3-20 12-18 Q6-5 19 10 Q4 16-7 22 Q-11 6-22-7Z" fill="#165fa1"/>
<path d="M12-18 Q22-9 23 3 Q7 0-3-11 Q4-17 12-18Z" fill="#f7e46d"/>
<path d="M19 10 Q12 22-2 23 Q-4 8 8-2 Q15 4 19 10Z" fill="#1a70ba"/>
<path d="M-22-7 Q-3-20 12-18 M12-18 Q22-9 23 3 M23 3 Q12 22-2 23 M-2 23 Q-16 17-22-7" fill="none" stroke="#fff" stroke-width="2"/>
<ellipse cx="-7" cy="-10" rx="7" ry="4" fill="#fff" opacity=".28"/></g>'''


def ball_svg(kind: str) -> str:
    if kind == "single_ball":
        content = ball_svg_fragment(50, 50, 38)
    elif kind == "ball_group":
        content = ball_svg_fragment(36, 57, 26) + ball_svg_fragment(66, 58, 26) + ball_svg_fragment(51, 31, 26)
    else:
        content = "".join(ball_svg_fragment(x, y, 22) for x, y in [(27, 64), (51, 65), (75, 64), (39, 42), (63, 41), (51, 21)])
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{content}</svg>'


def cart_svg(variant: str, fabric: str, compact: bool = False, folding: bool = False) -> str:
    top, bottom = (28, 80) if not compact else (36, 75)
    left, right = (15, 105) if not compact else (27, 93)
    balls = "".join(ball_svg_fragment(x, top + 7, 9) for x in range(left + 12, right, 19))
    support = ""
    if folding:
        support = '<path d="M25 82L96 137M96 82L25 137" stroke="#4d565d" stroke-width="6"/><path d="M25 82L96 137M96 82L25 137" stroke="#c4cbd0" stroke-width="2"/>'
    else:
        support = f'<path d="M{left+8} {bottom}L{left+5} 137M{right-8} {bottom}L{right-5} 137M{left+5} 104H{right-5}" stroke="#aeb8bc" stroke-width="5"/><path d="M{left+8} {bottom}L{left+5} 137M{right-8} {bottom}L{right-5} 137" stroke="#e7ecee" stroke-width="2"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 150">
<defs><linearGradient id="cloth" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{fabric}"/><stop offset="1" stop-color="#101a22"/></linearGradient><filter id="s"><feDropShadow dx="0" dy="3" stdDeviation="2" flood-opacity=".25"/></filter></defs>
<g filter="url(#s)"><ellipse cx="60" cy="142" rx="45" ry="5" fill="#1c282d" opacity=".2"/>{support}
<path d="M{left} {top}H{right}L{right-7} {bottom}H{left+7}Z" fill="url(#cloth)" stroke="#17252d" stroke-width="3"/>
<path d="M{left+5} {top+10}H{right-5}" stroke="#fff" stroke-opacity=".3" stroke-width="2"/>{balls}
<circle cx="{left+5}" cy="138" r="7" fill="#1e292e" stroke="#aeb8bc" stroke-width="2"/><circle cx="{right-5}" cy="138" r="7" fill="#1e292e" stroke="#aeb8bc" stroke-width="2"/></g></svg>'''


def equipment_svg(kind: str) -> str:
    label = kind.replace("_", " ").title()
    if "cone" in kind:
        body = '<path d="M20 78L50 18L80 78Z" fill="#ef7d43" stroke="#a43f20" stroke-width="4"/><rect x="10" y="75" width="80" height="12" rx="4" fill="#ef7d43" stroke="#a43f20" stroke-width="3"/><path d="M34 52H66" stroke="#fff" stroke-width="7"/>'
    elif "target" in kind or "hoop" in kind:
        body = '<circle cx="50" cy="50" r="37" fill="none" stroke="#e6c33d" stroke-width="9"/><circle cx="50" cy="50" r="17" fill="none" stroke="#176b62" stroke-width="6"/><path d="M8 50H92M50 8V92" stroke="#176b62" stroke-width="3"/>'
    elif "ladder" in kind:
        body = '<path d="M20 7V93M80 7V93M20 18H80M20 36H80M20 54H80M20 72H80M20 90H80" fill="none" stroke="#e0b82e" stroke-width="6"/>'
    elif "blocking" in kind:
        body = '<rect x="25" y="8" width="50" height="72" rx="9" fill="#235f87" stroke="#16384f" stroke-width="4"/><path d="M50 80V94M30 94H70" stroke="#616c70" stroke-width="7"/><path d="M35 22H65M35 35H65" stroke="#fff" stroke-opacity=".5" stroke-width="4"/>'
    else:
        body = f'<rect x="14" y="18" width="72" height="62" rx="9" fill="#355e58" stroke="#18322e" stroke-width="4"/><text x="50" y="55" text-anchor="middle" fill="#fff" font-family="Arial" font-size="12" font-weight="700">{label[:9]}</text>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><ellipse cx="50" cy="91" rx="35" ry="5" fill="#1b2926" opacity=".18"/>{body}</svg>'


def write_asset(relative: Path, content: str) -> str:
    path = ASSETS / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "/static/assets/" + relative.as_posix()


def main() -> None:
    manifest: list[dict] = []
    for role, poses in ROLE_POSES.items():
        teams = ["N"] if role == "coach" else ["A", "B"]
        for team in teams:
            for pose in poses:
                team_folder = "coach" if team == "N" else f"team_{team.lower()}"
                relative = Path("players") / team_folder / role / f"{slug(pose)}.svg"
                asset = write_asset(relative, player_svg(role, pose, team))
                manifest.append(
                    {
                        "id": f"{team.lower()}_{role}_{slug(pose)}",
                        "category": "player",
                        "role": role,
                        "pose": pose,
                        "team": "Neutral" if team == "N" else team,
                        "asset": asset,
                        "thumbnail": asset,
                        "defaultWidth": 72 if role != "coach" else 78,
                        "defaultHeight": 132 if "dive" in pose.lower() else 150,
                        "anchor": {"x": 0.5, "y": 1.0},
                    }
                )

    ball_kinds = [("single_ball", "Single Ball"), ("ball_group", "Ball Group"), ("ball_pile", "Ball Pile")]
    for kind, name in ball_kinds:
        asset = write_asset(Path("balls") / f"{kind}.svg", ball_svg(kind))
        manifest.append(
            {
                "id": kind,
                "category": "ball",
                "role": "",
                "pose": name,
                "team": "Neutral",
                "asset": asset,
                "thumbnail": asset,
                "defaultWidth": 46 if kind == "single_ball" else 72,
                "defaultHeight": 46 if kind == "single_ball" else 72,
                "anchor": {"x": 0.5, "y": 0.5},
            }
        )

    carts = [
        ("ball_cart_blue", "Ball Cart - Blue", "#246fa6", False, False),
        ("ball_cart_black", "Ball Cart - Black", "#252c32", False, False),
        ("compact_ball_cart", "Compact Ball Cart", "#22282c", True, False),
        ("folding_ball_cart", "Folding Ball Cart", "#1f2529", False, True),
    ]
    for asset_id, name, fabric, compact, folding in carts:
        asset = write_asset(Path("equipment") / "ball_carts" / f"{asset_id}.svg", cart_svg(asset_id, fabric, compact, folding))
        manifest.append(
            {
                "id": asset_id,
                "category": "equipment",
                "equipmentType": "ball_cart",
                "variant": name,
                "asset": asset,
                "thumbnail": asset,
                "defaultWidth": 106 if not compact else 88,
                "defaultHeight": 132 if not compact else 108,
                "anchor": {"x": 0.5, "y": 1.0},
            }
        )

    equipment = [
        ("cone", "Cone"),
        ("flat_marker", "Flat Marker"),
        ("target_mat", "Target Mat"),
        ("target_hoop", "Target Hoop"),
        ("floor_target", "Floor Target"),
        ("wall_target", "Wall Target"),
        ("blocking_board", "Blocking Board"),
        ("blocking_pad", "Blocking Pad"),
        ("blocking_dummy", "Blocking Dummy"),
        ("training_box", "Training Box"),
        ("bench", "Bench"),
        ("chair", "Chair"),
        ("agility_ladder", "Agility Ladder"),
        ("hurdle", "Hurdle"),
        ("scoreboard", "Scoreboard"),
    ]
    for asset_id, name in equipment:
        group = "blocking" if "blocking" in asset_id else "targets" if "target" in asset_id else "general"
        asset = write_asset(Path("equipment") / group / f"{asset_id}.svg", equipment_svg(asset_id))
        manifest.append(
            {
                "id": asset_id,
                "category": "equipment",
                "equipmentType": asset_id,
                "variant": name,
                "asset": asset,
                "thumbnail": asset,
                "defaultWidth": 68,
                "defaultHeight": 68,
                "anchor": {"x": 0.5, "y": 1.0},
            }
        )

    fallback = write_asset(Path("fallback.svg"), equipment_svg("asset"))
    manifest.append(
        {
            "id": "safe_fallback",
            "category": "fallback",
            "asset": fallback,
            "thumbnail": fallback,
            "defaultWidth": 70,
            "defaultHeight": 70,
            "anchor": {"x": 0.5, "y": 1.0},
        }
    )
    payload = {
        "schemaVersion": 1,
        "generatedBy": "Volleyball Practice Designer original SVG generator",
        "license": "Original project assets; no third-party marks or likenesses",
        "assets": manifest,
    }
    (ASSETS / "manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Generated {len(manifest)} assets at {ASSETS}")


if __name__ == "__main__":
    main()
