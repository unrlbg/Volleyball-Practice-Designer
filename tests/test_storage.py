import json

import pytest

from app.services.storage import JsonStore


def test_store_round_trip_and_order(tmp_path):
    store = JsonStore(tmp_path)
    store.save({"id": "a", "modified_at": "2026-01-01", "value": 1})
    store.save({"id": "b", "modified_at": "2026-01-02", "value": 2})
    assert [item["id"] for item in store.list()] == ["b", "a"]
    assert store.get("a")["value"] == 1
    assert json.loads((tmp_path / "a.json").read_text())["value"] == 1


def test_store_rejects_path_traversal(tmp_path):
    store = JsonStore(tmp_path)
    with pytest.raises(ValueError):
        store.get("../outside")


def test_store_handles_empty_and_non_object_json(tmp_path):
    store = JsonStore(tmp_path)
    (tmp_path / "empty.json").write_text("", encoding="utf-8")
    (tmp_path / "array.json").write_text("[]", encoding="utf-8")
    assert store.get("empty") is None
    assert store.get("array") is None
    assert store.list() == []
