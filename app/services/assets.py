from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.models.notes import normalize_object_note


def key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")


CHARACTER_VIEWS = (
    "Front",
    "3/4 Front Left",
    "3/4 Front Right",
    "Left Side",
    "Right Side",
    "3/4 Back Left",
    "3/4 Back Right",
    "Back",
    "45° Back",
)
DEFAULT_CHARACTER_VIEW = "Front"
VALID_ASSET_CATEGORIES = {"player", "experimental_player", "ball", "equipment", "fallback"}
VALID_PLAYER_ROLES = {"generic", "setter", "outside", "opposite", "middle", "libero", "coach"}
VALID_TEAMS = {"A", "B", "Neutral"}
CHARACTER_VIEW_ALIASES = {
    "front": "Front",
    "back": "Back",
    "left": "Left Side",
    "left_side": "Left Side",
    "right": "Right Side",
    "right_side": "Right Side",
    "3_4_front": "Front",
    "three_quarter_front": "Front",
    "34_front": "Front",
    "3_4_front_left": "3/4 Front Left",
    "three_quarter_front_left": "3/4 Front Left",
    "34_front_left": "3/4 Front Left",
    "3_4_front_right": "3/4 Front Right",
    "three_quarter_front_right": "3/4 Front Right",
    "34_front_right": "3/4 Front Right",
    "3_4_back": "Back",
    "three_quarter_back": "Back",
    "34_back": "Back",
    "3_4_back_left": "3/4 Back Left",
    "three_quarter_back_left": "3/4 Back Left",
    "34_back_left": "3/4 Back Left",
    "3_4_back_right": "3/4 Back Right",
    "three_quarter_back_right": "3/4 Back Right",
    "34_back_right": "3/4 Back Right",
    "45_back": "45° Back",
    "45_degree_back": "45° Back",
    "45_back_view": "45° Back",
}


def normalize_character_view(value: str | None) -> str:
    return CHARACTER_VIEW_ALIASES.get(key(value), DEFAULT_CHARACTER_VIEW)


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
        self.character_views: list[str] = list(payload.get("professionalCharacterViews") or CHARACTER_VIEWS)
        self.default_character_view: str = normalize_character_view(
            payload.get("defaultCharacterView") or DEFAULT_CHARACTER_VIEW
        )
        self.validation_warnings: list[str] = []
        raw_assets = payload.get("assets", [])
        self.diagnostics: dict[str, Any] = {
            "totalManifestEntries": len(raw_assets) if isinstance(raw_assets, list) else 0,
            "validEntries": 0,
            "invalidEntries": 0,
            "skippedEntries": 0,
            "filteredEntries": 0,
            "missingThumbnails": 0,
            "missingRuntimeFiles": 0,
            "professionalAssetsLoaded": 0,
            "skippedAssets": [],
        }
        if not isinstance(raw_assets, list):
            self._skip_asset("manifest", "Manifest assets must be a list", stage="load", kind="invalid")
            raw_assets = []
        self.all_assets: list[dict[str, Any]] = self._normalize_assets(raw_assets)
        self.all_by_id = {item["id"]: item for item in self.all_assets if "id" in item}
        self.library_assets: list[dict[str, Any]] = self._filter_valid_library_assets(self.all_assets)
        self.assets: list[dict[str, Any]] = [
            item for item in self.all_assets
            if self._is_editor_visible_asset(item)
        ]
        self._filter_invalid_editor_assets()
        self.by_id = {item["id"]: item for item in self.assets}
        self.validate_professional_catalog()
        self._finalize_diagnostics()

    def manifest(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "defaultPlayerVisualStyle": self.default_player_visual_style,
            "professionalPoseCatalog": self.professional_pose_catalog,
            "professionalPoseGroups": self.professional_pose_groups,
            "hiddenProfessionalRoles": self.hidden_professional_roles,
            "professionalCharacterViews": self.character_views,
            "defaultCharacterView": self.default_character_view,
            "validationWarnings": self.validation_warnings,
            "diagnostics": self.diagnostics,
            "assets": self.assets,
            "libraryAssets": self.library_assets,
        }

    def startup_report(self) -> str:
        return "\n".join(
            [
                f"Professional assets loaded: {self.diagnostics['professionalAssetsLoaded']}",
                f"Professional assets released: {self.diagnostics.get('professionalAssetsReleased', 0)}",
                f"Professional assets hidden: {self.diagnostics.get('professionalAssetsHidden', 0)}",
                f"Professional assets filtered: {self.diagnostics.get('professionalAssetsHidden', 0)}",
                f"45° Back assets loaded: {self.diagnostics.get('back45AssetsLoaded', 0)}",
                f"45° Back assets released: {self.diagnostics.get('back45AssetsReleased', 0)}",
                f"45° Back assets hidden: {self.diagnostics.get('back45AssetsHidden', 0)}",
                f"Skipped assets: {self.diagnostics['skippedEntries']}",
                f"Missing thumbnails: {self.diagnostics['missingThumbnails']}",
                f"Missing runtime files: {self.diagnostics['missingRuntimeFiles']}",
                f"Invalid manifest entries: {self.diagnostics['invalidEntries']}",
            ]
        )

    def _skip_asset(self, asset_id: str, reason: str, *, stage: str, kind: str) -> None:
        self.diagnostics["skippedEntries"] += 1
        if kind == "invalid":
            self.diagnostics["invalidEntries"] += 1
        elif kind == "filtered":
            self.diagnostics["filteredEntries"] += 1
        entry = {"id": asset_id, "stage": stage, "kind": kind, "reason": reason}
        self.diagnostics["skippedAssets"].append(entry)
        self._warn_validation(f"{asset_id} skipped from {stage}: {reason}")

    def _normalize_assets(self, raw_assets: list[Any]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index, item in enumerate(raw_assets):
            if not isinstance(item, dict):
                self._skip_asset(f"manifest[{index}]", "entry is not an object", stage="load", kind="invalid")
                continue
            asset_id = str(item.get("id") or "").strip()
            if not asset_id:
                self._skip_asset(f"manifest[{index}]", "missing id", stage="load", kind="invalid")
                continue
            if asset_id in seen:
                self._skip_asset(asset_id, "duplicate asset ID", stage="load", kind="invalid")
                continue
            seen.add(asset_id)
            normalized.append(self._normalize_asset(item))
        return normalized

    def _finalize_diagnostics(self) -> None:
        library_professional = [
            asset for asset in self.library_assets
            if asset.get("category") == "player"
            and asset.get("visualStyle") == "professional"
        ]
        all_professional = [
            asset for asset in self.all_assets
            if asset.get("category") == "player"
            and asset.get("visualStyle") == "professional"
        ]
        all_back45 = [
            asset for asset in all_professional
            if asset.get("view") == "45° Back"
        ]
        released_professional = [asset for asset in all_professional if self._is_editor_visible_asset(asset)]
        hidden_professional = [asset for asset in all_professional if not self._is_editor_visible_asset(asset)]
        released_back45 = [asset for asset in all_back45 if self._is_editor_visible_asset(asset)]
        hidden_back45 = [asset for asset in all_back45 if not self._is_editor_visible_asset(asset)]
        self.diagnostics["validEntries"] = len(self.library_assets)
        self.diagnostics["loadedAssets"] = len(self.library_assets)
        self.diagnostics["releasedAssets"] = len([asset for asset in self.library_assets if self._is_editor_visible_asset(asset)])
        self.diagnostics["hiddenAssets"] = len(hidden_professional)
        self.diagnostics["professionalAssetsLoaded"] = len(library_professional)
        self.diagnostics["professionalAssetsReleased"] = len(released_professional)
        self.diagnostics["professionalAssetsHidden"] = len(hidden_professional)
        self.diagnostics["back45AssetsLoaded"] = len(all_back45)
        self.diagnostics["back45AssetsReleased"] = len(released_back45)
        self.diagnostics["back45AssetsHidden"] = len(hidden_back45)

    def _normalize_asset(self, item: dict[str, Any]) -> dict[str, Any]:
        asset = deepcopy(item)
        if not (
            asset.get("category") == "player"
            and asset.get("visualStyle") == "professional"
        ):
            return asset
        self._promote_approved_professional_asset(asset)
        view = normalize_character_view(asset.get("view") or asset.get("characterView"))
        asset["view"] = view
        asset["characterView"] = view
        asset.setdefault("availableCharacterViews", [])
        return asset

    @staticmethod
    def _promote_approved_professional_asset(asset: dict[str, Any]) -> None:
        release_status = str(asset.get("releaseStatus", ""))
        release_state = str(asset.get("releaseState", ""))
        if (
            asset.get("visibleInEditor") is False
            or release_status.startswith("hidden")
            or release_state.startswith("hidden")
        ):
            return
        approved = asset.get("isApproved") is True or str(asset.get("releaseState", "")).lower() == "approved"
        if not approved:
            return
        asset["releaseStatus"] = "released"
        asset["releaseState"] = "released"
        asset["visibleInEditor"] = True
        asset["isReleased"] = True
        asset["isVisible"] = True
        asset["isEnabled"] = True

    @staticmethod
    def _is_editor_visible_asset(asset: dict[str, Any]) -> bool:
        if not (
            asset.get("category") == "player"
            and asset.get("visualStyle") == "professional"
        ):
            return True
        for flag in ("visibleInEditor", "isReleased", "isVisible", "isEnabled"):
            if asset.get(flag) is False:
                return False
        release_status = str(asset.get("releaseStatus", "released"))
        release_state = str(asset.get("releaseState", "released"))
        return not release_status.startswith("hidden") and release_state not in {"false", "hidden", "unreleased"}

    def _available_views(self, *, role: str, team: str, pose_key: str) -> list[str]:
        views = {
            item["view"] for item in self.assets
            if item.get("category") == "player"
            and item.get("visualStyle") == "professional"
            and item.get("role") == role
            and item.get("team") == team
            and key(item.get("pose")) == pose_key
        }
        return [view for view in self.character_views if view in views]

    def _warn_validation(self, message: str) -> None:
        self.validation_warnings.append(message)

    def _filter_invalid_editor_assets(self) -> None:
        static_root = self.manifest_path.parents[1]
        ids: set[str] = set()
        combos: set[tuple[str | None, str | None, str, str | None]] = set()
        valid: list[dict[str, Any]] = []
        required_fields = {"id", "category", "asset", "thumbnail", "defaultWidth", "defaultHeight"}
        for item in self.assets:
            asset_id = str(item.get("id") or "unknown")
            missing = required_fields - item.keys()
            if missing:
                self._warn_validation(f"{asset_id} skipped: missing {sorted(missing)}")
                continue
            if asset_id in ids:
                self._warn_validation(f"{asset_id} skipped: duplicate asset ID")
                continue
            ids.add(asset_id)
            if item.get("category") == "player" and item.get("visualStyle") == "professional":
                combo = (item.get("team"), item.get("role"), key(item.get("pose")), item.get("view"))
                if combo in combos:
                    self._warn_validation(f"{asset_id} skipped: duplicate Professional role/pose/team/view")
                    continue
                combos.add(combo)
            invalid_path = False
            for field in ("asset", "thumbnail"):
                value = item.get(field)
                if not isinstance(value, str) or not value.startswith("/static/") or ".." in value:
                    self._warn_validation(f"{asset_id} skipped: invalid {field} path {value!r}")
                    invalid_path = True
                    break
                local = static_root / value.removeprefix("/static/")
                if not local.is_file():
                    self._warn_validation(f"{asset_id} skipped: missing {field} file {local}")
                    invalid_path = True
                    break
            if invalid_path:
                continue
            valid.append(item)
        self.assets = valid

    def _filter_valid_library_assets(self, assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        static_root = self.manifest_path.parents[1]
        valid: list[dict[str, Any]] = []
        required_fields = {"id", "category", "asset", "thumbnail", "defaultWidth", "defaultHeight"}
        for item in assets:
            asset_id = str(item.get("id") or "unknown")
            if not self._is_editor_visible_asset(item):
                self._skip_asset(asset_id, "hidden or not released", stage="Asset Library", kind="filtered")
                continue
            missing = required_fields - item.keys()
            if missing:
                self._skip_asset(asset_id, f"missing {sorted(missing)}", stage="Asset Library", kind="invalid")
                continue
            category = item.get("category")
            if category not in VALID_ASSET_CATEGORIES:
                self._skip_asset(asset_id, f"invalid category {category!r}", stage="Asset Library", kind="invalid")
                continue
            if category == "player":
                role = item.get("role")
                if role not in VALID_PLAYER_ROLES:
                    self._skip_asset(asset_id, f"invalid role {role!r}", stage="Asset Library", kind="invalid")
                    continue
                team = item.get("team")
                if team not in VALID_TEAMS:
                    self._skip_asset(asset_id, f"invalid team {team!r}", stage="Asset Library", kind="invalid")
                    continue
                pose = item.get("pose")
                if not isinstance(pose, str) or not pose.strip():
                    self._skip_asset(asset_id, "invalid pose", stage="Asset Library", kind="invalid")
                    continue
                if item.get("visualStyle") == "professional":
                    view = item.get("view") or item.get("characterView")
                    if view not in self.character_views:
                        self._skip_asset(asset_id, f"invalid view {view!r}", stage="Asset Library", kind="invalid")
                        continue
            invalid_path = False
            for field in ("asset", "thumbnail"):
                value = item.get(field)
                if not isinstance(value, str) or not value.startswith("/static/") or ".." in value:
                    self._skip_asset(asset_id, f"invalid {field} path {value!r}", stage="Asset Library", kind="invalid")
                    invalid_path = True
                    break
                local = static_root / value.removeprefix("/static/")
                if not local.is_file():
                    if field == "thumbnail":
                        self.diagnostics["missingThumbnails"] += 1
                    else:
                        self.diagnostics["missingRuntimeFiles"] += 1
                    self._skip_asset(asset_id, f"missing {field} file {local}", stage="Asset Library", kind="invalid")
                    invalid_path = True
                    break
            if invalid_path:
                continue
            valid.append(item)
        return valid

    def validate_professional_catalog(self) -> None:
        """Record manifest warnings without making the editor unusable."""
        if not self.professional_pose_catalog:
            self._warn_validation("Professional pose catalog is missing")
            return
        ids: set[str] = set()
        static_root = self.manifest_path.parents[1]
        required_fields = {
            "id", "characterId", "role", "pose", "team", "asset", "thumbnail",
            "defaultWidth", "defaultHeight", "footAnchor", "view", "characterView",
        }
        professional = [
            item for item in self.assets
            if item.get("category") == "player"
            and item.get("visualStyle") == "professional"
        ]
        for item in professional:
            missing = required_fields - item.keys()
            if missing:
                self._warn_validation(f'{item.get("id", "Professional asset")} missing {sorted(missing)}')
                continue
            if item["id"] in ids:
                self._warn_validation(f'Duplicate Professional asset ID: {item["id"]}')
                continue
            ids.add(item["id"])
            if item["defaultWidth"] <= 0 or item["defaultHeight"] <= 0:
                self._warn_validation(f'Invalid dimensions for {item["id"]}')
                continue
            for anchor_field in ("anchor", "footAnchor"):
                anchor = item.get(anchor_field)
                if (
                    not isinstance(anchor, dict)
                    or not 0 <= anchor.get("x", -1) <= 1
                    or not 0 <= anchor.get("y", -1) <= 1
                ):
                    self._warn_validation(f'Invalid {anchor_field} for {item["id"]}')
            for field in ("asset", "thumbnail"):
                local = static_root / item[field].removeprefix("/static/")
                if not local.is_file():
                    self._warn_validation(f'Missing {field} file for {item["id"]}: {local}')
            if item["view"] not in self.character_views:
                self._warn_validation(f'{item["id"]} has unsupported Professional view: {item["view"]}')
            if item["characterView"] != item["view"]:
                self._warn_validation(f'{item["id"]} has inconsistent view metadata')
            if "mirroredFrom" in item:
                self._warn_validation(f'{item["id"]} cannot be mirrored from another Professional view')

        for role, poses in self.professional_pose_catalog.items():
            teams = ("Neutral",) if role == "coach" else ("A", "B")
            for team in teams:
                for pose in poses:
                    matches = [
                        item for item in professional
                        if item["role"] == role and item["team"] == team
                        and key(item["pose"]) == key(pose)
                        and item["view"] == self.default_character_view
                    ]
                    any_view_matches = [
                        item for item in professional
                        if item["role"] == role and item["team"] == team
                        and key(item["pose"]) == key(pose)
                    ]
                    team_a_fallback_matches = [
                        item for item in professional
                        if team == "B"
                        and item["role"] == role and item["team"] == "A"
                        and key(item["pose"]) == key(pose)
                    ]
                    if len(matches) > 1 or (not matches and not any_view_matches and not team_a_fallback_matches):
                        self._warn_validation(
                            f"Professional catalog requires exactly one {team} "
                            f"{role}/{pose}/{self.default_character_view} asset; found {len(matches)}"
                        )

    def resolve_player(
        self,
        team: str | None,
        role: str | None,
        pose: str | None,
        visual_style: str = "professional",
        character_view: str | None = None,
    ) -> dict[str, Any]:
        role_key = self.ROLE_ALIASES.get(key(role), key(role) or "generic")
        team_key = "Neutral" if role_key == "coach" else (team if team in {"A", "B"} else "A")
        pose_key = self.POSE_ALIASES.get(key(pose), key(pose))
        explicit_view = character_view is not None
        view = normalize_character_view(character_view or self.default_character_view)
        candidates = [
            item
            for item in self.assets
            if item.get("category") == "player"
            and item.get("role") == role_key
            and item.get("team") == team_key
            and item.get("visualStyle") == "professional"
        ]
        for item in candidates:
            if key(item.get("pose")) == pose_key and item.get("view") == view:
                return item
        pose_exists = any(key(item.get("pose")) == pose_key for item in candidates)
        if pose_exists:
            available = self._available_views(role=role_key, team=team_key, pose_key=pose_key)
            if explicit_view:
                raise ValueError(
                    f"No Professional {view} asset for {team_key} {role_key}/{pose_key}; "
                    f"available views: {available or ['none']}"
                )
        if team_key == "B":
            for item in self.assets:
                if (
                    item.get("category") == "player"
                    and item.get("role") == role_key
                    and item.get("team") == "A"
                    and item.get("visualStyle") == "professional"
                    and key(item.get("pose")) == pose_key
                    and item.get("view") == view
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
            if key(item.get("pose")) == default_pose and item.get("view") == view:
                return item
        raise ValueError(f"No Professional asset for {team_key} {role_key}/{pose_key}")

    def resolve_equipment(self, label: str | None) -> dict[str, Any]:
        label_key = key(label)
        asset_id = self.EQUIPMENT_ALIASES.get(label_key, label_key)
        return self.by_id.get(asset_id, self.by_id["safe_fallback"])

    def migrate_object(self, source: dict[str, Any]) -> dict[str, Any]:
        obj = deepcopy(source)
        obj["note"] = normalize_object_note(obj.get("note"))
        existing = obj.get("assetId")
        existing_asset = self.by_id.get(existing) or self.all_by_id.get(existing)
        if obj.get("type") in {"player", "character"}:
            role = obj.get("role") or obj.get("label") or existing_asset and existing_asset.get("role")
            pose = obj.get("pose") or existing_asset and existing_asset.get("pose")
            team = obj.get("team") or existing_asset and existing_asset.get("team")
            requested_view = (
                obj.get("characterView")
                or obj.get("view")
                or existing_asset and existing_asset.get("characterView")
            )
            try:
                asset = self.resolve_player(
                    team,
                    role,
                    pose,
                    character_view=requested_view,
                )
            except ValueError:
                asset = self.resolve_player(team, role, None, character_view=self.default_character_view)
            obj["type"] = "character"
            obj["role"] = role or asset["role"]
            obj["pose"] = asset["pose"] if key(pose) != key(asset["pose"]) else pose
            obj["team"] = "Neutral" if asset["role"] == "coach" else (
                team if team in {"A", "B"} else asset["team"]
            )
            obj["visualStyle"] = "professional"
            obj["characterView"] = asset["characterView"]
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
