from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db.session import get_session
from app.engine.cache import cache
from app.models.event import Event, EventCreate, EventRead, EventType

router = APIRouter(prefix="/events", tags=["events"])

# Tipos de evento que REQUIEREN entity_id para poder medir CTR en el Módulo 11
_REQUIRES_ENTITY_ID = {
    EventType.recommendation_shown,
    EventType.recommendation_clicked,
    EventType.recommendation_feedback,
}
_FEEDBACK_TYPES = {"like", "hide", "not_interested", "dislike"}


def _validate_recommendation_feedback(payload: EventCreate) -> None:
    if payload.event_type != EventType.recommendation_feedback:
        return

    properties = payload.properties or {}
    product_id = properties.get("product_id")
    feedback_type = properties.get("feedback_type")
    rank_position = properties.get("rank_position")

    if not isinstance(product_id, str) or not product_id.strip():
        raise HTTPException(
            status_code=422,
            detail="recommendation_feedback requiere properties.product_id.",
        )

    if feedback_type not in _FEEDBACK_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                "recommendation_feedback requiere properties.feedback_type "
                f"con uno de estos valores: {sorted(_FEEDBACK_TYPES)}."
            ),
        )

    if rank_position is not None and (
        not isinstance(rank_position, int) or rank_position < 1
    ):
        raise HTTPException(
            status_code=422,
            detail="properties.rank_position debe ser un entero positivo.",
        )


def _validate_recommendation_clicked(payload: EventCreate) -> None:
    """Módulo 9: recommendation_clicked debe incluir properties.product_id.

    Sin este campo, el CTR por ítem es incalculable porque no sabemos qué
    producto específico fue clickeado dentro de la lista recomendada.
    entity_id ya es validado como obligatorio por _REQUIRES_ENTITY_ID.
    """
    if payload.event_type != EventType.recommendation_clicked:
        return

    properties = payload.properties or {}
    product_id = properties.get("product_id")

    if not isinstance(product_id, str) or not product_id.strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "recommendation_clicked requiere properties.product_id "
                "(product_id del ítem clickeado, string no vacío)."
            ),
        )


def _validate_recommendation_shown(payload: EventCreate) -> None:
    """Módulo 9: si recommendation_shown incluye product_ids, debe ser lista.

    No se requiere product_ids (el backend lo registra automáticamente desde
    /recommendations). Pero si el cliente lo envía manualmente, debe ser una
    lista para que las queries de top-productos funcionen correctamente.
    """
    if payload.event_type != EventType.recommendation_shown:
        return

    properties = payload.properties or {}
    product_ids = properties.get("product_ids")

    if product_ids is not None and not isinstance(product_ids, list):
        raise HTTPException(
            status_code=422,
            detail="recommendation_shown: properties.product_ids debe ser una lista.",
        )


@router.post("", response_model=EventRead, status_code=201)
def create_event(
    payload: EventCreate,
    session: Session = Depends(get_session),
) -> EventRead:
    """
    Ingesta un evento de comportamiento.

    Regla de negocio crítica: los eventos de tipo recommendation_shown y
    recommendation_clicked requieren entity_id (= recommendation_id del Módulo 11)
    para que el CTR sea medible.
    """
    if payload.event_type in _REQUIRES_ENTITY_ID and not payload.entity_id:
        raise HTTPException(
            status_code=422,
            detail=(
                f"El campo 'entity_id' es obligatorio cuando event_type es "
                f"'{payload.event_type.value}'. Debe contener el recommendation_id "
                "generado por el motor de recomendaciones (Módulo 11)."
            ),
        )
    _validate_recommendation_feedback(payload)
    _validate_recommendation_clicked(payload)   # Módulo 9: requiere product_id
    _validate_recommendation_shown(payload)      # Módulo 9: product_ids debe ser lista si viene

    event = Event(
        event_type=payload.event_type,
        customer_id=payload.customer_id,
        session_id=payload.session_id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        properties=payload.properties,
        # Siempre UTC, nunca provisto por el cliente
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        schema_version=1,
    )

    session.add(event)
    session.commit()
    session.refresh(event)
    if payload.event_type == EventType.recommendation_feedback:
        cache.clear()
    return EventRead.model_validate(event)


@router.get("", response_model=list[EventRead])
def list_events(
    customer_id: Optional[str] = Query(default=None, description="Filtrar por customer_id"),
    event_type: Optional[EventType] = Query(default=None, description="Filtrar por tipo de evento"),
    limit: int = Query(default=50, ge=1, le=200, description="Máximo de resultados (1-200)"),
    session: Session = Depends(get_session),
) -> list[EventRead]:
    """
    Consulta eventos con filtros opcionales, ordenados por timestamp descendente.
    """
    query = select(Event)

    if customer_id:
        query = query.where(Event.customer_id == customer_id)
    if event_type:
        query = query.where(Event.event_type == event_type)

    query = query.order_by(Event.timestamp.desc()).limit(limit)  # type: ignore[union-attr]

    events = session.exec(query).all()
    return [EventRead.model_validate(e) for e in events]
