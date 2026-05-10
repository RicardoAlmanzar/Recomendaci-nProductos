"""
Rutas de Recomendaciones — Módulo 11.

POST /recommendations  → Genera recomendaciones (con cache)
GET  /recommendations/{recommendation_id}  → Busca por ID (debugging)
"""
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.engine.cache import cache
from app.engine.candidates import get_candidates
from app.engine.ranker import rank
from app.models import Cliente, Compra, Regla
from app.models.recommendation import (
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

ALGO_VERSION = os.getenv("ALGO_VERSION", "rules_v1")


@router.post("", response_model=RecommendationResponse)
def recommend(
    request: RecommendationRequest,
    session: Session = Depends(get_session),
):
    """
    Genera recomendaciones para un cliente.
    Pipeline: Cache → Candidatos → Ranking → Response con recommendation_id.
    """
    # ── 1. Cache lookup ─────────────────────────────────────────────────
    request_key = cache.make_request_key(
        request.customer_id, request.session_id, request.page_type, request.slot
    )
    cached = cache.get(request_key)
    if cached is not None:
        cached["cache_hit"] = True
        return cached

    # ── 2. Obtener cliente ──────────────────────────────────────────────
    customer = session.get(Cliente, request.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # ── 3. Candidatos ───────────────────────────────────────────────────
    candidates = get_candidates(request, session)

    # ── 4. Ranking ──────────────────────────────────────────────────────
    affinity_rules = session.exec(select(Regla)).all()
    purchases = session.exec(
        select(Compra).where(Compra.customer_id == request.customer_id)
    ).all()

    ranked = rank(
        candidates=candidates,
        customer=customer,
        affinity_rules=affinity_rules,
        purchases=purchases,
        limit=request.limit,
    )

    # ── 5. Construir items con category y rank_position ─────────────────
    # Mapa rápido product_id → category desde los candidatos cargados
    cat_map = {p.product_id: p.category for p in candidates}

    items = [
        RecommendationItem(
            product_id=r["product_id"],
            sku=r["sku"],
            name=r["name"],
            category=cat_map.get(r["product_id"], "unknown"),
            score=r["score"],
            rank_position=idx + 1,
            reason_codes=r["reason_codes"],
        )
        for idx, r in enumerate(ranked)
    ]

    # ── 6. Construir response ───────────────────────────────────────────
    recommendation_id = str(uuid.uuid4())

    response = RecommendationResponse(
        recommendation_id=recommendation_id,
        customer_id=request.customer_id,
        session_id=request.session_id,
        page_type=request.page_type,
        slot=request.slot,
        items=items,
        algo_version=ALGO_VERSION,
        generated_at=datetime.now(timezone.utc),
        cache_hit=False,
    )

    # ── 7. Guardar en cache (dos keys: por request y por ID) ────────────
    response_dict = response.model_dump()
    # Serializar datetime a ISO string para el cache
    response_dict["generated_at"] = response.generated_at.isoformat()
    cache.set(request_key, response_dict)
    cache.set(cache.make_id_key(recommendation_id), response_dict)

    return response


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation_by_id(recommendation_id: str):
    """
    Busca una recomendación por su ID en el cache.
    Útil para debugging y auditoría.
    """
    id_key = cache.make_id_key(recommendation_id)
    cached = cache.get(id_key)
    if cached is not None:
        return cached

    raise HTTPException(
        status_code=404,
        detail="Recomendación no encontrada o expirada. Las recomendaciones "
               "se mantienen en cache por un tiempo limitado.",
    )