from fastapi import APIRouter, Query
from typing import Optional
from ..models import search_materials, search_suggestions, log_search_event, get_recent_materials

router = APIRouter(prefix="/search", tags=["search"])


def _fts_query(q: str) -> str:
    q = q.strip()
    if not q:
        return q
    if q.endswith("*"):
        return q
    return q + "*"


@router.get("/")
def search_endpoint(q: str = Query(...), limit: int = Query(20), offset: int = Query(0)):
    results = search_materials(_fts_query(q), limit=limit, offset=offset)
    clicked = None
    if results:
        clicked = results[0]["id"]
    log_search_event(q, clicked_material_id=clicked, no_result=len(results) == 0)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/suggest")
def suggest_endpoint(q: str = Query(...), limit: int = Query(5)):
    return search_suggestions(_fts_query(q), limit=limit)


@router.get("/recent")
def recent_endpoint(limit: int = Query(10)):
    return get_recent_materials(limit=limit)


