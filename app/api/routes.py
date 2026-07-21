from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import Drill, Practice

router = APIRouter(prefix="/api")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_get(store, item_id: str):
    try:
        return store.get(item_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def safe_delete(store, item_id: str) -> bool:
    try:
        return store.delete(item_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "product": "Volleyball Practice Designer"}


@router.get("/assets")
def list_assets(request: Request):
    return request.app.state.assets.manifest()


@router.get("/drills")
def list_drills(request: Request):
    return [request.app.state.assets.migrate_drill(item) for item in request.app.state.drills.list()]


@router.post("/drills", status_code=201)
def create_drill(payload: Drill, request: Request):
    payload.modified_at = now()
    data = request.app.state.assets.migrate_drill(payload.model_dump())
    return request.app.state.drills.save(data)


@router.get("/drills/{drill_id}")
def get_drill(drill_id: str, request: Request):
    item = safe_get(request.app.state.drills, drill_id)
    if item is None:
        raise HTTPException(404, "Drill not found")
    return request.app.state.assets.migrate_drill(item)


@router.put("/drills/{drill_id}")
def update_drill(drill_id: str, payload: Drill, request: Request):
    current = safe_get(request.app.state.drills, drill_id)
    if current is None:
        raise HTTPException(404, "Drill not found")
    data = payload.model_dump()
    data["id"] = drill_id
    data["created_at"] = current.get("created_at", data["created_at"])
    data["modified_at"] = now()
    data = request.app.state.assets.migrate_drill(data)
    return request.app.state.drills.save(data)


@router.post("/drills/{drill_id}/duplicate", status_code=201)
def duplicate_drill(drill_id: str, request: Request):
    item = safe_get(request.app.state.drills, drill_id)
    if item is None:
        raise HTTPException(404, "Drill not found")
    copy = request.app.state.assets.migrate_drill(deepcopy(item))
    copy["id"] = str(uuid4())
    copy["metadata"]["name"] = f'{copy["metadata"].get("name", "Untitled")} - Copy'
    copy["created_at"] = copy["modified_at"] = now()
    return request.app.state.drills.save(copy)


@router.delete("/drills/{drill_id}", status_code=204)
def delete_drill(drill_id: str, request: Request):
    if not safe_delete(request.app.state.drills, drill_id):
        raise HTTPException(404, "Drill not found")


@router.get("/practices")
def list_practices(request: Request):
    return request.app.state.practices.list()


@router.post("/practices", status_code=201)
def create_practice(payload: Practice, request: Request):
    payload.modified_at = now()
    return request.app.state.practices.save(payload.model_dump())


@router.get("/practices/{practice_id}")
def get_practice(practice_id: str, request: Request):
    item = safe_get(request.app.state.practices, practice_id)
    if item is None:
        raise HTTPException(404, "Practice not found")
    return item


@router.put("/practices/{practice_id}")
def update_practice(practice_id: str, payload: Practice, request: Request):
    current = safe_get(request.app.state.practices, practice_id)
    if current is None:
        raise HTTPException(404, "Practice not found")
    data = payload.model_dump()
    data["id"] = practice_id
    data["created_at"] = current.get("created_at", data["created_at"])
    data["modified_at"] = now()
    return request.app.state.practices.save(data)


@router.post("/practices/{practice_id}/duplicate", status_code=201)
def duplicate_practice(practice_id: str, request: Request):
    item = safe_get(request.app.state.practices, practice_id)
    if item is None:
        raise HTTPException(404, "Practice not found")
    copy = deepcopy(item)
    copy["id"] = str(uuid4())
    copy["name"] = f'{copy.get("name", "Untitled")} - Copy'
    copy["created_at"] = copy["modified_at"] = now()
    return request.app.state.practices.save(copy)


@router.delete("/practices/{practice_id}", status_code=204)
def delete_practice(practice_id: str, request: Request):
    if not safe_delete(request.app.state.practices, practice_id):
        raise HTTPException(404, "Practice not found")
