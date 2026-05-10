from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.event import Event, EventCreate, EventRead, EventType

router = APIRouter(prefix="/events", tags=["events"])

# Tipos de evento que REQUIEREN entity_id para poder medir CTR en el Módulo 11
_REQUIRES_ENTITY_ID = {EventType.recommendation_shown, EventType.recommendation_clicked}


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
