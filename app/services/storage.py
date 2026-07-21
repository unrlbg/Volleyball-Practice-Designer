from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


class JsonStore:
    """Small, atomic, filesystem-backed document store."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _path(self, item_id: str) -> Path:
        if not item_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in item_id):
            raise ValueError("Invalid item id")
        return self.base_dir / f"{item_id}.json"

    def list(self) -> list[dict[str, Any]]:
        items = []
        for path in self.base_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    items.append(data)
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
        return sorted(items, key=lambda item: item.get("modified_at", ""), reverse=True)

    def get(self, item_id: str) -> dict[str, Any] | None:
        path = self._path(item_id)
        if not path.exists():
            return None
        try:
            content = path.read_text(encoding="utf-8")
            if not content.strip():
                return None
            data = json.loads(content)
            return data if isinstance(data, dict) else None
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None

    def save(self, item: dict[str, Any]) -> dict[str, Any]:
        path = self._path(item["id"])
        tmp = path.with_suffix(".tmp")
        with self._lock:
            tmp.write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(path)
        return item

    def delete(self, item_id: str) -> bool:
        path = self._path(item_id)
        if not path.exists():
            return False
        path.unlink()
        return True
