from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app" / "static" / "assets" / "manifest.json"
ROLE_ORDER = ["setter", "outside", "opposite", "middle", "libero", "coach"]


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    front_poses: dict[str, list[str]] = {role: [] for role in ROLE_ORDER}
    for asset in payload["assets"]:
        if not (
            asset.get("category") == "player"
            and asset.get("visualStyle") == "professional"
            and asset.get("view") == "Front"
            and asset.get("visibleInEditor", True) is not False
            and asset.get("releaseStatus", "released") == "released"
        ):
            continue
        role = asset.get("role")
        pose = asset.get("pose")
        if role not in front_poses or pose in front_poses[role]:
            continue
        front_poses[role].append(pose)

    payload["professionalPoseCatalog"] = {
        role: front_poses[role]
        for role in ROLE_ORDER
        if front_poses[role]
    }
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Rebuilt Professional front pose catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
