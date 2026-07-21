from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4


def key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")


class AssetRegistry:
    """Loads and resolves the renderer-neutral visual asset manifest."""

    ROLE_ALIASES = {
        "generic_player": "generic",
        "player": "generic",
    }
    POSE_ALIASES = {
        "attack_starting_position": "attack_start",
        "approach": "approach_step_1",
        "defensive_position": "defensive_position",
        "front_set": "front_set",
        "back_set": "back_set",
        "slide_approach": "slide_approach",
    }
    EQUIPMENT_ALIASES = {
        "ball": "single_ball",
        "volleyball": "single_ball",
        "ball_group": "ball_group",
        "ball_pile": "ball_pile",
        "ball_cart": "ball_cart_blue",
        "ball_cart_blue": "ball_cart_blue",
        "ball_cart_black": "ball_cart_black",
        "compact_ball_cart": "compact_ball_cart",
        "folding_ball_cart": "folding_ball_cart",
    }

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.schema_version = payload["schemaVersion"]
        self.default_player_visual_style = payload.get("defaultPlayerVisualStyle", "professional")
        self.professional_pose_catalog: dict[str, list[str]] = payload.get("professionalPoseCatalog", {})
        self.professional_pose_groups: dict[str, dict[str, list[str]]] = payload.get(
            "professionalPoseGroups", {}
        )
        self.hidden_professional_roles: list[str] = payload.get("hiddenProfessionalRoles", [])
        self.assets: list[dict[str, Any]] = payload["assets"]
        self.by_id = {item["id"]: item for item in self.assets}
        self.validate_professional_catalog()

    def manifest(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "defaultPlayerVisualStyle": self.default_player_visual_style,
            "professionalPoseCatalog": self.professional_pose_catalog,
            "professionalPoseGroups": self.professional_pose_groups,
            "hiddenProfessionalRoles": self.hidden_professional_roles,
            "assets": self.assets,
        }

    def validate_professional_catalog(self) -> None:
        """Fail startup when any editor-visible Professional asset is invalid."""
        if not self.professional_pose_catalog:
            raise ValueError("Professional pose catalog is missing")
        ids: set[str] = set()
        static_root = self.manifest_path.parents[1]
        required_fields = {
            "id", "characterId", "role", "pose", "team", "asset", "thumbnail",
            "defaultWidth", "defaultHeight", "footAnchor",
        }
        professional = [
            item for item in self.assets
            if item.get("category") == "player"
            and item.get("visualStyle") == "professional"
        ]
        for item in professional:
            missing = required_fields - item.keys()
            if missing:
                raise ValueError(f'{item.get("id", "Professional asset")} missing {sorted(missing)}')
            if item["id"] in ids:
                raise ValueError(f'Duplicate Professional asset ID: {item["id"]}')
            ids.add(item["id"])
            if item["defaultWidth"] <= 0 or item["defaultHeight"] <= 0:
                raise ValueError(f'Invalid dimensions for {item["id"]}')
            for anchor_field in ("anchor", "footAnchor"):
                anchor = item.get(anchor_field)
                if (
                    not isinstance(anchor, dict)
                    or not 0 <= anchor.get("x", -1) <= 1
                    or not 0 <= anchor.get("y", -1) <= 1
                ):
                    raise ValueError(f'Invalid {anchor_field} for {item["id"]}')
            for field in ("asset", "thumbnail"):
                local = static_root / item[field].removeprefix("/static/")
                if not local.is_file():
                    raise ValueError(f'Missing {field} file for {item["id"]}: {local}')

        for role, poses in self.professional_pose_catalog.items():
            teams = ("Neutral",) if role == "coach" else ("A", "B")
            for team in teams:
                for pose in poses:
                    matches = [
                        item for item in professional
                        if item["role"] == role and item["team"] == team
                        and key(item["pose"]) == key(pose)
                    ]
                    if len(matches) != 1:
                        raise ValueError(
                            f"Professional catalog requires exactly one {team} "
                            f"{role}/{pose} asset; found {len(matches)}"
                        )

    def resolve_player(
        self,
        team: str | None,
        role: str | None,
        pose: str | None,
        visual_style: str = "professional",
    ) -> dict[str, Any]:
        role_key = self.ROLE_ALIASES.get(key(role), key(role) or "generic")
        team_key = "Neutral" if role_key == "coach" else (team if team in {"A", "B"} else "A")
        pose_key = self.POSE_ALIASES.get(key(pose), key(pose))
        candidates = [
            item
            for item in self.assets
            if item.get("category") == "player"
            and item.get("role") == role_key
            and item.get("team") == team_key
            and item.get("visualStyle") == "professional"
        ]
        for item in candidates:
            if key(item.get("pose")) == pose_key:
                return item
        if team_key == "B":
            for item in self.assets:
                if (
                    item.get("category") == "player"
                    and item.get("role") == role_key
                    and item.get("team") == "A"
                    and item.get("visualStyle") == "professional"
                    and key(item.get("pose")) == pose_key
                ):
                    return item
        default_pose = {
            "setter": "ready",
            "outside": "ready",
            "opposite": "attack_start",
            "middle": "ready",
            "libero": "reception",
            "coach": "holding_ball",
        }.get(role_key)
        for item in candidates:
            if key(item.get("pose")) == default_pose:
                return item
        raise ValueError(f"No Professional asset for {team_key} {role_key}/{pose_key}")

    def resolve_equipment(self, label: str | None) -> dict[str, Any]:
        label_key = key(label)
        asset_id = self.EQUIPMENT_ALIASES.get(label_key, label_key)
        return self.by_id.get(asset_id, self.by_id["safe_fallback"])

    def migrate_object(self, source: dict[str, Any]) -> dict[str, Any]:
        obj = deepcopy(source)
        existing = obj.get("assetId")
        existing_asset = self.by_id.get(existing)
        if obj.get("type") in {"player", "character"}:
            role = obj.get("role") or obj.get("label") or existing_asset and existing_asset.get("role")
            pose = obj.get("pose") or existing_asset and existing_asset.get("pose")
            team = obj.get("team") or existing_asset and existing_asset.get("team")
            asset = self.resolve_player(
                team,
                role,
                pose,
            )
            obj["type"] = "character"
            obj["role"] = role or asset["role"]
            obj["pose"] = asset["pose"] if key(pose) != key(asset["pose"]) else pose
            obj["team"] = "Neutral" if asset["role"] == "coach" else (
                team if team in {"A", "B"} else asset["team"]
            )
            obj["visualStyle"] = "professional"
            obj["characterId"] = asset["characterId"]
            obj["assetId"] = asset["id"]
            obj.pop("isProfessionalFallback", None)
            obj.setdefault("width", asset["defaultWidth"])
            obj.setdefault("height", asset["defaultHeight"])
            obj.setdefault("anchor", asset.get("anchor", {"x": 0.5, "y": 1.0}))
            obj.setdefault("mirrorX", obj.get("mirror", False))
            obj.setdefault("flipY", False)
            obj.setdefault("showShadow", True)
            obj.setdefault("zIndex", obj.get("layer", 1))
            obj.setdefault("assignedCourtId", obj.get("courtId"))
            return obj
        if existing in self.by_id:
            return obj
        if obj.get("type") == "equipment":
            asset = self.resolve_equipment(obj.get("label"))
        else:
            asset = self.by_id["safe_fallback"] if existing else None
        if asset:
            obj["assetId"] = asset["id"]
            obj.setdefault("width", asset["defaultWidth"])
            obj.setdefault("height", asset["defaultHeight"])
            obj.setdefault("anchor", asset.get("anchor", {"x": 0.5, "y": 1.0}))
        return obj

    @staticmethod
    def default_court(
        legacy_settings: dict[str, Any] | None = None,
        *,
        court_id: str | None = None,
        name: str = "Court 1",
        x: float = 600,
        y: float = 390,
        width: float = 780,
    ) -> dict[str, Any]:
        legacy = legacy_settings or {}
        settings = legacy.get("settings", legacy)
        court_width = legacy.get("width", width)
        return {
            "id": court_id or str(uuid4()),
            "type": "court",
            "name": legacy.get("name", name),
            "x": legacy.get("x", x),
            "y": legacy.get("y", y),
            "width": court_width,
            "height": court_width / 2,
            "rotation": legacy.get("rotation", 0) % 360,
            "locked": legacy.get("locked", False),
            "style": legacy.get("style", "competition"),
            "kind": legacy.get("kind", "court"),
            "rotateContentsWithCourt": legacy.get("rotateContentsWithCourt", False),
            "keepPlayersUpright": legacy.get("keepPlayersUpright", True),
            "settings": {
                "showAttackLines": settings.get("showAttackLines", settings.get("attackLines", True)),
                "showZoneLabels": settings.get("showZoneLabels", settings.get("zones", True)),
                "showNet": settings.get("showNet", settings.get("net", True)),
                "showGrid": settings.get("showGrid", settings.get("grid", False)),
                "showAntennas": settings.get("showAntennas", settings.get("antennas", True)),
            },
        }

    def migrate_frame(self, source: dict[str, Any]) -> dict[str, Any]:
        frame = deepcopy(source)
        courts = frame.get("courts")
        if not isinstance(courts, list) or not courts:
            legacy = frame.get("court", {})
            courts = [self.default_court(legacy)]
        else:
            courts = [
                self.default_court(
                    court,
                    court_id=court.get("id"),
                    name=court.get("name", f"Court {index + 1}"),
                    x=court.get("x", 600 + index * 840),
                    y=court.get("y", 390),
                    width=court.get("width", 780),
                )
                for index, court in enumerate(courts)
            ]
        frame["courts"] = courts
        frame["court"] = {
            "attackLines": courts[0]["settings"]["showAttackLines"],
            "zones": courts[0]["settings"]["showZoneLabels"],
            "grid": courts[0]["settings"]["showGrid"],
            "antennas": courts[0]["settings"]["showAntennas"],
            "net": courts[0]["settings"]["showNet"],
        }
        valid_ids = {court["id"] for court in courts}
        default_id = courts[0]["id"]
        migrated_objects = []
        for source_obj in frame.get("objects", []):
            obj = self.migrate_object(source_obj)
            assigned_court = obj.get("assignedCourtId", obj.get("courtId"))
            if assigned_court not in valid_ids:
                assigned_court = default_id
            obj["courtId"] = assigned_court
            obj["assignedCourtId"] = assigned_court
            migrated_objects.append(obj)
        frame["objects"] = migrated_objects
        return frame

    def migrate_drill(self, source: dict[str, Any]) -> dict[str, Any]:
        drill = deepcopy(source)
        drill["schema_version"] = max(3, drill.get("schema_version", 1))
        legacy_court = drill.get("court", {})
        frames = drill.get("frames", [])
        if not frames:
            frames = [{"id": str(uuid4()), "name": "Frame 1", "court": legacy_court, "objects": []}]
        drill["frames"] = [
            self.migrate_frame({**frame, "court": frame.get("court", legacy_court)})
            for frame in frames
        ]
        first = drill["frames"][0]["courts"][0]["settings"]
        drill["court"] = {
            "attackLines": first["showAttackLines"],
            "zones": first["showZoneLabels"],
            "grid": first["showGrid"],
            "antennas": first["showAntennas"],
            "net": first["showNet"],
        }
        return drill
