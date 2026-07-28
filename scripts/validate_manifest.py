from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.assets import AssetRegistry  # noqa: E402

MANIFEST = ROOT / "app" / "static" / "assets" / "manifest.json"


def main() -> int:
    registry = AssetRegistry(MANIFEST)
    print(f"Manifest parsed: {MANIFEST}")
    print(f"Visible assets: {len(registry.assets)}")
    print(f"Validation warnings: {len(registry.validation_warnings)}")
    for warning in registry.validation_warnings:
        print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
