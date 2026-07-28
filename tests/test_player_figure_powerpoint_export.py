from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

from PIL import Image


ROLES = ("setter", "outside", "opposite", "middle", "libero", "coach")


def professional_player_assets(client, role: str | None = None):
    payload = client.get("/api/assets").json()
    assets = [
        item for item in payload["libraryAssets"]
        if item.get("category") == "player"
        and item.get("visualStyle") == "professional"
        and item.get("role") in ROLES
    ]
    if role:
        assets = [item for item in assets if item["role"] == role]
    return assets


def slide_count(path: Path) -> int:
    with ZipFile(path) as pptx:
        return sum(1 for name in pptx.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml"))


def image_count(path: Path) -> int:
    with ZipFile(path) as pptx:
        return sum(1 for name in pptx.namelist() if name.startswith("ppt/media/image") and name.endswith(".png"))


def deck_text(path: Path) -> str:
    with ZipFile(path) as pptx:
        values = []
        for name in pptx.namelist():
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                root = ElementTree.fromstring(pptx.read(name))
                values.extend(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
        return "\n".join(values)


def assert_export_folder(payload: dict) -> Path:
    folder = Path(payload["folder"])
    assert folder.name == "player_figures"
    assert folder.parent.name == "exports"
    assert folder.exists()
    return folder


def test_export_button_and_dialog_exist(client):
    html = client.get("/").text
    assert 'id="export-player-figures"' in html
    assert "Export Player Figures" in html
    assert 'id="player-figure-export-dialog"' in html
    assert 'name="player-figure-selection"' in html
    assert 'name="player-figure-format"' in html


def test_all_figures_pptx_is_created_without_png_pack(client):
    expected = professional_player_assets(client)
    response = client.post("/api/exports/player-figures", json={"mode": "all", "format": "pptx"})
    assert response.status_code == 200
    payload = response.json()
    folder = assert_export_folder(payload)
    path = Path(payload["decks"][0]["path"])
    assert path == folder / "all_player_figures.pptx"
    assert path.exists()
    assert slide_count(path) == len(expected)
    assert image_count(path) == len(expected)
    assert payload["pngPaths"] == []


def test_role_specific_pptx_slide_count_matches_assets(client):
    expected = professional_player_assets(client, "middle")
    response = client.post("/api/exports/player-figures", json={"mode": "role", "role": "middle", "format": "pptx"})
    assert response.status_code == 200
    path = Path(response.json()["decks"][0]["path"])
    assert path.name == "middle.pptx"
    assert slide_count(path) == len(expected)
    text = deck_text(path)
    assert "Role: Middle" in text
    assert "Export Player Figures" not in text
    assert "Asset Library" not in text


def test_png_pack_files_are_transparent_and_clearly_named(client):
    expected = professional_player_assets(client, "setter")
    response = client.post("/api/exports/player-figures", json={"mode": "role", "role": "setter", "format": "png"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["decks"] == []
    assert len(payload["pngPaths"]) == len(expected)
    first = Path(payload["pngPaths"][0])
    assert first.parent.name == "png"
    assert "setter" in first.name
    assert "team" in first.name
    with Image.open(first) as image:
        assert image.mode == "RGBA"
        alpha_min, alpha_max = image.getchannel("A").getextrema()
        assert alpha_min < 255
        assert alpha_max == 255


def test_both_exports_pptx_and_png_pack(client):
    expected = professional_player_assets(client, "libero")
    response = client.post("/api/exports/player-figures", json={"mode": "role", "role": "libero", "format": "both"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["decks"]) == 1
    assert len(payload["pngPaths"]) == len(expected)
    path = Path(payload["decks"][0]["path"])
    assert path.name == "libero.pptx"
    assert slide_count(path) == len(expected)
    assert image_count(path) == len(expected)


def test_selected_only_export_works(client):
    selected = professional_player_assets(client)[:3]
    response = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "pptx", "assetIds": [item["id"] for item in selected]})
    assert response.status_code == 200
    path = Path(response.json()["decks"][0]["path"])
    assert path.name == "selected_figures.pptx"
    assert slide_count(path) == 3
    text = deck_text(path)
    for item in selected:
        assert item["id"] in text
        assert Path(item["asset"]).name in text


def test_no_legacy_vector_figures_are_exported(client):
    legacy = next(
        item for item in client.get("/api/assets").json()["assets"]
        if item.get("category") == "player" and item.get("visualStyle") == "legacy_vector"
    )
    response = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "pptx", "assetIds": [legacy["id"]]})
    assert response.status_code == 400
    assert "Invalid player figure asset id" in response.json()["detail"]


def test_invalid_or_missing_asset_is_handled_safely(client):
    response = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "png", "assetIds": ["missing-asset"]})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid player figure asset id: missing-asset"

    empty = client.post("/api/exports/player-figures", json={"mode": "selected", "format": "png", "assetIds": []})
    assert empty.status_code == 400
    assert empty.json()["detail"] == "Select at least one player figure to export"
