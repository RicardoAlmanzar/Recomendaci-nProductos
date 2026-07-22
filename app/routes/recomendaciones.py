"""
Rutas de Recomendaciones — Módulo 11.

POST /recommendations  → Genera recomendaciones (con cache)
GET  /recommendations/{recommendation_id}  → Busca por ID (debugging)
"""
import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.engine.cache import cache
from app.engine.candidates import get_candidates
from app.engine.feedback import get_feedback_signals
from app.engine.ranker import RankingContext, rank
from app.engine.popularity import get_popularity_scores
from app.models import Cliente, Compra, Regla, Producto
from app.models.recommendation import (
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
)
from app.models.event import EventType
from app.services.campaigns import get_active_offer_scores
from app.services.metrics import register_event

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
        request.customer_id, request.session_id, request.page_type, request.slot, request.context
    )
    cached = cache.get(request_key)
    if cached is not None:
        cached["cache_hit"] = True
        # ── Módulo 9: registrar recommendation_shown aunque sea cache-hit ──────────
        _cached_product_ids = [
            item["product_id"] for item in cached.get("items", [])
        ]
        if _cached_product_ids:  # solo registrar si hay ítems que mostrar
            register_event(
                session=session,
                event_type=EventType.recommendation_shown,
                customer_id=request.customer_id,
                session_id=request.session_id,
                entity_id=cached["recommendation_id"],
                entity_type="recommendation",
                properties={
                    "product_ids": _cached_product_ids,
                    "item_count": len(_cached_product_ids),
                    "page_type": request.page_type,
                    "slot": request.slot,
                    "algo_version": cached.get("algo_version", ALGO_VERSION),
                    "cache_hit": True,
                },
            )
        return cached

    # ── 2. Obtener cliente ──────────────────────────────────────────────
    customer = session.get(Cliente, request.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # ── 3. Candidatos ───────────────────────────────────────────────────
    candidates = get_candidates(request, session)

    # ── 4. Ranking (Módulo 5) ───────────────────────────────────────────
    affinity_rules = session.exec(select(Regla)).all()
    purchases = session.exec(
        select(Compra).where(Compra.customer_id == request.customer_id)
    ).all()

    # Pre-cargar las categorías de los productos comprados para que scorer.py las use
    # de manera robusta incluso si los candidatos están filtrados por contexto.
    purchased_product_ids = {p.product_id for p in purchases}
    if purchased_product_ids:
        products_db = session.exec(
            select(Producto).where(Producto.product_id.in_(list(purchased_product_ids)))
        ).all()
        cat_map = {p.product_id: p.category for p in products_db}
        for p in purchases:
            p.__dict__["category"] = cat_map.get(p.product_id)

    # ── Módulo 7: Cold-start popularity ─────────────────────────────────
    popularity_scores = {}
    if len(purchases) == 0:
        popularity_scores = get_popularity_scores(session)
    feedback_signals = get_feedback_signals(
        customer_id=request.customer_id,
        session_id=request.session_id,
        session=session,
    )
    channel = (request.context or {}).get("channel")
    offer_scores = get_active_offer_scores(session, channel=channel)

    ranking_context = RankingContext(
        customer=customer,
        purchases=purchases,
        affinity_rules=affinity_rules,
        limit=request.limit,
        popularity_scores=popularity_scores,
        feedback_signals=feedback_signals,
        offer_scores=offer_scores,
        page_type=request.page_type,
        slot=request.slot,
        session_id=request.session_id,
        request_context=request.context,
    )

    ranked = rank(candidates=candidates, context=ranking_context)

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

    # ── Módulo 9: registrar recommendation_shown (denominador de CTR) ───────────
    # Decisión: no registrar si item_count == 0 para no distorsionar el
    # denominador. Un response sin ítems no es una impresión de recomendación.
    _product_ids = [item.product_id for item in items]
    if _product_ids:
        register_event(
            session=session,
            event_type=EventType.recommendation_shown,
            customer_id=request.customer_id,
            session_id=request.session_id,
            entity_id=recommendation_id,
            entity_type="recommendation",
            properties={
                "product_ids": _product_ids,
                "item_count": len(_product_ids),
                "page_type": request.page_type,
                "slot": request.slot,
                "algo_version": ALGO_VERSION,
                "cache_hit": False,
            },
        )

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
