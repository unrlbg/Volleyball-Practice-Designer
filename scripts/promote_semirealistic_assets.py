from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "app" / "static" / "assets"
MANIFEST = ASSETS / "manifest.json"
SOURCE = ASSETS / "experimental" / "style_c" / "runtime"
SOURCE_THUMBS = ASSETS / "experimental" / "style_c" / "thumbs"

POSES = [
    ("team_a_setter_ready_semirealistic", "A", "setter", "Ready", "setter_ready", "setter/ready"),
    ("team_a_setter_front_set_semirealistic", "A", "setter", "Front Set", "setter_front_set", "setter/front_set"),
    ("team_b_setter_back_set_semirealistic", "B", "setter", "Back Set", "setter_back_set", "setter/back_set"),
    ("team_b_setter_jump_set_semirealistic", "B", "setter", "Jump Set", "setter_jump_set", "setter/jump_set"),
    ("team_a_outside_jump_attack_semirealistic", "A", "outside", "Jump Attack", "outside_attack", "outside/jump_attack"),
    ("team_b_middle_single_block_semirealistic", "B", "middle", "Single Block", "middle_block", "middle/single_block"),
    ("team_a_outside_reception_semirealistic", "A", "outside", "Reception", "libero_reception", "outside/reception"),
    ("team_b_libero_dig_semirealistic", "B", "libero", "Dig", "libero_dig", "libero/dig"),
    ("team_a_outside_dive_semirealistic", "A", "outside", "Dive", "libero_dive", "outside/dive"),
    ("coach_holding_ball_semirealistic", "Neutral", "coach", "Holding Ball", "coach_holding_ball", "coach/holding_ball"),
    ("team_a_generic_ready_semirealistic", "A", "generic", "Ready", "team_a_ready", "generic/ready"),
    ("team_b_generic_ready_semirealistic", "B", "generic", "Ready", "team_b_ready", "generic/ready"),
    ("team_a_generic_standing_semirealistic", "A", "generic", "Standing", "team_a_ready", "generic/standing"),
    ("team_b_generic_standing_semirealistic", "B", "generic", "Standing", "team_b_ready", "generic/standing"),
    ("team_a_libero_reception_semirealistic", "A", "libero", "Reception", "libero_reception", "libero/reception"),
    ("team_a_libero_dive_semirealistic", "A", "libero", "Dive", "libero_dive", "libero/dive"),
    ("team_b_setter_ready_semirealistic", "B", "setter", "Ready", "team_b_ready", "setter/ready"),
    ("team_b_libero_reception_semirealistic", "B", "libero", "Reception", "team_b_ready", "libero/reception"),
    ("team_a_middle_ready_semirealistic", "A", "middle", "Ready", "team_a_ready", "middle/ready"),
    ("team_b_middle_ready_semirealistic", "B", "middle", "Ready", "team_b_ready", "middle/ready"),
    ("team_a_outside_ready_semirealistic", "A", "outside", "Ready", "team_a_ready", "outside/ready"),
    ("team_b_outside_ready_semirealistic", "B", "outside", "Ready", "team_b_ready", "outside/ready"),
    ("team_a_opposite_ready_semirealistic", "A", "opposite", "Ready", "team_a_ready", "opposite/ready"),
    ("team_b_opposite_ready_semirealistic", "B", "opposite", "Ready", "team_b_ready", "opposite/ready"),
    ("coach_standing_semirealistic", "Neutral", "coach", "Standing", "coach_holding_ball", "coach/standing"),
]


def main() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = payload["assets"]
    for item in assets:
        if item.get("category") == "player":
            item.setdefault("visualStyle", "legacy_vector")

    promoted_ids = {row[0] for row in POSES}
    assets[:] = [item for item in assets if item["id"] not in promoted_ids]
    for asset_id, team, role, pose, source_name, relative in POSES:
        team_dir = "neutral" if team == "Neutral" else f"team_{team.lower()}"
        asset_rel = Path("players") / "semi_realistic" / team_dir / f"{relative}.webp"
        thumb_rel = Path("thumbnails") / "players" / "semi_realistic" / team_dir / f"{relative}.webp"
        asset_path = ASSETS / asset_rel
        thumb_path = ASSETS / thumb_rel
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / f"{source_name}.webp", asset_path)
        shutil.copy2(SOURCE_THUMBS / f"{source_name}.webp", thumb_path)
        assets.append(
            {
                "id": asset_id,
                "category": "player",
                "role": role,
                "pose": pose,
                "poseKey": pose.lower().replace(" ", "_"),
                "team": team,
                "visualStyle": "semi_realistic",
                "asset": f"/static/assets/{asset_rel.as_posix()}",
                "thumbnail": f"/static/assets/{thumb_rel.as_posix()}",
                "defaultWidth": 78 if role != "coach" else 76,
                "defaultHeight": 160,
                "anchor": {"x": 0.5, "y": 1.0},
                "source": "/static/assets/experimental/sources/style_c_sheet_alpha.png",
            }
        )

    payload["generatedBy"] = "Volleyball Practice Designer asset pipeline"
    payload["defaultPlayerVisualStyle"] = "semi_realistic"
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
