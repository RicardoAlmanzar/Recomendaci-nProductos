import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Index
from sqlmodel import Column, Field, SQLModel
from sqlalchemy.dialects.postgresql import JSONB


# ---------------------------------------------------------------------------
# Enum — sagrado: no cambiar valores sin migración de datos
# ---------------------------------------------------------------------------

class EventType(str, Enum):
    product_view = "product_view"
    product_click = "product_click"
    search = "search"
    add_to_cart = "add_to_cart"
    purchase = "purchase"
    recommendation_shown = "recommendation_shown"
    recommendation_clicked = "recommendation_clicked"
    recommendation_feedback = "recommendation_feedback"


# ---------------------------------------------------------------------------
# Modelo de tabla
# ---------------------------------------------------------------------------

class Event(SQLModel, table=True):
    """
    Tabla de eventos de comportamiento del usuario.
    Schema v1 — no modificar campos sin migración explícita.
    """
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_customer_id", "customer_id"),
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_timestamp", "timestamp"),
    )

    # PK: UUID generado en el servidor, nunca provisto por el cliente
    event_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
    )

    # Tipo de evento — obligatorio
    event_type: EventType = Field(nullable=False, index=False)

    # Identificador del cliente registrado — nullable (puede ser sesión anónima futura)
    customer_id: Optional[str] = Field(
        default=None,
        nullable=True,
        max_length=50,
        foreign_key="customers.customer_id",
    )

    # Sesión anónima — reservado para implementación futura
    session_id: Optional[str] = Field(default=None, nullable=True, max_length=255)

    # Qué tipo de entidad involucra el evento: "product", "search", "recommendation"
    entity_type: Optional[str] = Field(default=None, nullable=True, max_length=50)

    # Identificador de la entidad (product_id o recommendation_id del Módulo 11)
    entity_id: Optional[str] = Field(default=None, nullable=True, max_length=255)

    # Metadata libre — almacenada como JSONB en PostgreSQL
    properties: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )

    # Timestamp UTC — asignado siempre en el servidor
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )

    # Versión del schema — permite detectar registros viejos en migraciones futuras
    schema_version: int = Field(default=1, nullable=False)


# ---------------------------------------------------------------------------
# Schemas Pydantic para la API (separados del modelo de tabla)
# ---------------------------------------------------------------------------

class EventCreate(SQLModel):
    """Payload que el cliente envía. Solo event_type es obligatorio."""
    event_type: EventType
    customer_id: Optional[str] = None
    session_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    properties: Optional[dict[str, Any]] = None
    # timestamp y schema_version se asignan en el servidor; no se exponen aquí


class EventRead(SQLModel):
    """Payload que el endpoint devuelve, incluyendo campos generados por el servidor."""
    event_id: uuid.UUID
    event_type: EventType
    customer_id: Optional[str] = None
    session_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    properties: Optional[dict[str, Any]] = None
    timestamp: datetime
    schema_version: int
