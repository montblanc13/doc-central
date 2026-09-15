from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.config import Settings, get_settings
from app.services import TypesenseService

router = APIRouter(prefix="/api")


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
) -> dict:
    return service.search(q, page=page, per_page=per_page)
