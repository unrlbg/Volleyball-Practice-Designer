from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app" / "static" / "assets" / "manifest.json"
DEFENSIVE_GROUPS = {
    "General Defense",
    "Court Coverage",
    "Digging",
    "Diving",
    "After Defense",
}
QUALITY_HOLD_REASON = (
    "Hidden because the current 45-degree defensive figures are not accepted "
    "as Professional Character Library quality."
)


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hidden = 0
    for asset in payload["assets"]:
        if str(asset.get("id", "")).startswith("professional_45_back_"):
            asset["visibleInEditor"] = False
            asset["releaseStatus"] = "hidden_quality_hold"
            asset["qualityHoldReason"] = QUALITY_HOLD_REASON
            asset["sourceQualityReference"] = "professional_45_back_defensive_library_hidden_pending_reference"
            hidden += 1

    groups = payload.get("professionalPoseGroups", {})
    for role, role_groups in groups.items():
        for group_name in list(role_groups):
            if group_name in DEFENSIVE_GROUPS:
                del role_groups[group_name]

    catalog = payload.setdefault("professionalPoseCatalog", {})
    for role, role_groups in groups.items():
        catalog[role] = unique([
            pose
            for poses in role_groups.values()
            for pose in poses
        ])

    notes = payload.setdefault("heroPack", {}).setdefault("notes", [])
    hidden_note = "45° Back Defensive Character Library hidden pending Professional replacement"
    notes[:] = [note for note in notes if note != "45° Back Defensive Character Library"]
    if hidden_note not in notes:
        notes.append(hidden_note)

    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Hidden {hidden} unaccepted 45-degree defensive assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
