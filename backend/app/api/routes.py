from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status

from app.config import Settings, get_settings
from app.models import ID_PATTERN, MetadataDocument, MetadataDocumentUpdate
from app.services import DocumentAlreadyExists, DocumentNotFound, TypesenseService

router = APIRouter(prefix="/api")

DocumentId = Annotated[
    str,
    Path(
        min_length=1,
        max_length=128,
        pattern=ID_PATTERN,
        description="Identifiant opaque du document",
    ),
]


def get_typesense(settings: Annotated[Settings, Depends(get_settings)]) -> TypesenseService:
    return TypesenseService(settings)


Service = Annotated[TypesenseService, Depends(get_typesense)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/search")
def search(
    service: Service,
    q: str = Query(default="", max_length=500),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> dict:
    return service.search(q, page=page, per_page=per_page)


@router.post("/documents", status_code=status.HTTP_201_CREATED)
def create_document(service: Service, document: MetadataDocument) -> dict:
    try:
        return service.create(document)
    except DocumentAlreadyExists as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Le document '{document.id}' existe déjà.",
        ) from error


@router.get("/documents/{document_id}")
def read_document(service: Service, document_id: DocumentId) -> dict:
    try:
        return service.get(document_id)
    except DocumentNotFound as error:
        raise _not_found(document_id) from error


@router.put("/documents/{document_id}")
def replace_document(service: Service, document_id: DocumentId, document: MetadataDocument) -> dict:
    if document.id != document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'identifiant du corps de requête doit correspondre à celui de l'URL.",
        )
    return service.upsert(document)


@router.patch("/documents/{document_id}")
def update_document(
    service: Service, document_id: DocumentId, changes: MetadataDocumentUpdate
) -> dict:
    if not changes.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun champ à mettre à jour.",
        )
    try:
        return service.update(document_id, changes)
    except DocumentNotFound as error:
        raise _not_found(document_id) from error


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(service: Service, document_id: DocumentId) -> Response:
    try:
        service.delete(document_id)
    except DocumentNotFound as error:
        raise _not_found(document_id) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _not_found(document_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document '{document_id}' introuvable.",
    )
