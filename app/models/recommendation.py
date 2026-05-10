"""
Schemas del Módulo 11 — API de Recomendaciones.
Contrato inmutable: no cambiar campos ni estructura sin coordinación con el frontend.
"""
from datetime import datetime
from typing import Any, List, Optional

from sqlmodel import SQLModel, Field


# ---------------------------------------------------------------------------
# Request — lo que el frontend envía
# ---------------------------------------------------------------------------

class RecommendationRequest(SQLModel):
    """Payload de entrada para solicitar recomendaciones."""
    customer_id: str
    session_id: Optional[str] = None
    page_type: str          # homepage | product_detail | cart | search
    slot: str               # hero | sidebar | related | you_may_like
    limit: int = Field(default=10, le=20)  # máximo 20
    context: Optional[dict[str, Any]] = None  # ej. {"category": "packaging"}


# ---------------------------------------------------------------------------
# Item individual — cada producto en la lista de respuesta
# ---------------------------------------------------------------------------

class RecommendationItem(SQLModel):
    """Un producto recomendado con su posición y justificación."""
    product_id: str
    sku: str
    name: str
    category: str
    score: float
    rank_position: int          # posición 1-based
    reason_codes: List[str]


# ---------------------------------------------------------------------------
# Response completa — contrato inmutable del endpoint
# ---------------------------------------------------------------------------

class RecommendationResponse(SQLModel):
    """Respuesta del endpoint POST /recommendations."""
    recommendation_id: str      # UUID — usar en eventos recommendation_shown/clicked
    customer_id: str
    session_id: Optional[str] = None
    page_type: str
    slot: str
    items: List[RecommendationItem]
    algo_version: str           # ej. "rules_v1"
    generated_at: datetime
    cache_hit: bool