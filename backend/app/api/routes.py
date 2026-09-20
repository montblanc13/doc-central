from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.config import Settings, get_settings
from app.services import TypesenseService
from app.services.typesense import SortOrder

router = APIRouter(prefix="/api")
SearchSortField = Literal["relevance", "title", "updated_at", "source_name", "format"]


def get_typesense(settings: Annotated[Settings, Depends(get_settings)]) -> TypesenseService:
    return TypesenseService(settings)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/search")
def search(
    service: Annotated[TypesenseService, Depends(get_typesense)],
    q: str = Query(default="", max_length=500),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    format_filter: Annotated[str | None, Query(alias="format", max_length=50)] = None,
    sort_by: Annotated[SearchSortField, Query()] = "relevance",
    sort_order: Annotated[SortOrder, Query()] = "asc",
) -> dict:
    return service.search(
        q,
        page=page,
        per_page=per_page,
        format_filter=format_filter,
        sort_by=None if sort_by == "relevance" else sort_by,
        sort_order=sort_order,
    )
