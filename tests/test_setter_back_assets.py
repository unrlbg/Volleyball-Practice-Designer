from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest
from PIL import Image

from app.services.assets import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
MANIFEST = STATIC / "assets" / "manifest.json"

SETTER_BACK_POSES = [
    "Ready",
    "Front Set",
    "Back Set",
    "Jump Set",
    "One-Hand Set",
    "Setter Dump",
    "Transition",
    "Defensive Ready",
    "Emergency Set",
]


def local(path: str) -> Path:
    return STATIC / path.removeprefix("/static/")


def slide_count(path: Path) -> int:
    with ZipFile(path) as deck:
        return sum(1 for name in deck.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))


@pytest.fixture(scope="module")
def registry() -> AssetRegistry:
    return AssetRegistry(MANIFEST)


@pytest.mark.parametrize("team", ["A", "B"])
@pytest.mark.parametrize("pose", SETTER_BACK_POSES)
def test_released_setter_back_assets_resolve_to_professional_cutouts(registry, team, pose):
    asset = registry.resolve_player(team, "setter", pose, character_view="Back")

    assert asset["role"] == "setter"
    assert asset["team"] == team
    assert asset["pose"] == pose
    assert asset["view"] == "Back"
    assert asset["visualStyle"] == "professional"
    assert asset["releaseStatus"] == "released"
    assert asset["visibleInEditor"] is True
    assert asset["professionalGrade"] is True
    assert asset["supportsMirror"] is False
    assert asset["facingSupport"] == []
    assert asset["containsNet"] is False
    assert asset["containsCourt"] is False
    assert asset["sourceQualityReference"] == "professional_team_a_middle_jump_block_back"
    assert not asset["asset"].endswith(".svg")
    for field in ("master", "asset", "thumbnail"):
        assert local(asset[field]).is_file()


@pytest.mark.parametrize("team", ["A", "B"])
def test_setter_back_assets_are_transparent_and_clean(registry, team):
    for pose in SETTER_BACK_POSES:
        asset = registry.resolve_player(team, "setter", pose, character_view="Back")
        with Image.open(local(asset["master"])) as master, Image.open(local(asset["asset"])) as runtime:
            assert master.format == "PNG"
            assert master.mode == "RGBA"
            assert max(master.size) >= 900
            assert runtime.format == "WEBP"
            assert runtime.mode == "RGBA"
            assert runtime.getchannel("A").getextrema()[0] == 0
            assert runtime.height <= 520


def test_setter_back_only_poses_do_not_get_front_placeholders(registry):
    for pose in ["Jump Set", "One-Hand Set", "Setter Dump", "Transition", "Defensive Ready", "Emergency Set"]:
        with pytest.raises(ValueError, match="No Professional Front asset"):
            registry.resolve_player("A", "setter", pose, character_view="Front")


def test_setter_back_export_and_save_reload(client, registry):
    asset = registry.resolve_player("A", "setter", "Front Set", character_view="Back")

    export = client.post(
        "/api/exports/player-figures",
        json={"mode": "selected", "format": "pptx", "assetIds": [asset["id"]]},
    )
    assert export.status_code == 200
    deck = Path(export.json()["decks"][0]["path"])
    assert deck.is_file()
    assert slide_count(deck) == 1

    payload = {
        "metadata": {"name": "Setter back view"},
        "frames": [{
            "id": "frame-one",
            "objects": [{
                "id": "setter",
                "type": "character",
                "team": "A",
                "role": "setter",
                "pose": "Front Set",
                "characterView": "Back",
                "assetId": asset["id"],
                "x": 420,
                "y": 360,
            }],
        }],
    }
    saved = client.post("/api/drills", json=payload)
    assert saved.status_code == 201
    loaded = client.get(f'/api/drills/{saved.json()["id"]}').json()
    player = loaded["frames"][0]["objects"][0]

    assert player["pose"] == "Front Set"
    assert player["characterView"] == "Back"
    assert player["assetId"] == asset["id"]
