from __future__ import annotations

import os
import webbrowser
from pathlib import Path
from threading import Timer

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.services.storage import JsonStore
from app.services.assets import AssetRegistry

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv("VPD_DATA_DIR", ROOT / "data"))


def create_app() -> FastAPI:
    app = FastAPI(title="Volleyball Practice Designer", version="0.1.0")
    app.state.drills = JsonStore(DATA / "drills")
    app.state.practices = JsonStore(DATA / "practices")
    app.state.assets = AssetRegistry(ROOT / "app" / "static" / "assets" / "manifest.json")
    app.include_router(router)
    app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(ROOT / "app" / "templates" / "index.html")

    return app


app = create_app()


if __name__ == "__main__":
    host, port = "127.0.0.1", 8765
    if os.getenv("VPD_NO_BROWSER") != "1":
        Timer(1.1, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    uvicorn.run("app.main:app", host=host, port=port, reload=False)

