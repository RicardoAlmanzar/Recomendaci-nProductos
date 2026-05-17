"""
Capa de candidatos — Módulo 11 + Módulo 7 (cold-start).

Responsabilidad: dado un request, devolver los objetos Producto candidatos
que el ranker procesará.  Esta capa NO hace scoring ni excluye compras
previas (eso lo hace el scorer internamente).
"""
from __future__ import annotations

from sqlmodel import Session, select

from app.engine.popularity import get_popular_product_ids
from app.models.compra import Compra
from app.models.producto import Producto
from app.models.recommendation import RecommendationRequest


def get_candidates(
    request: RecommendationRequest,
    session: Session,
) -> list[Producto]:
    """
    Retorna los productos candidatos para el ranker.

    - Carga productos activos.
    - Si context contiene "category", filtra por ella.
    - Pool mínimo: limit * 3 para darle material al ranker.
    - Cold-start (Módulo 7): combina productos populares reales
      (por frecuencia de compra) con productos de alta strategic_priority,
      eliminando duplicados y respetando pool_size.
      Si no hay purchases suficientes, cae al fallback por strategic_priority.
    """
    pool_size = request.limit * 3

    # ── Detectar cold-start ─────────────────────────────────────────────
    has_history = session.exec(
        select(Compra).where(Compra.customer_id == request.customer_id)
    ).first() is not None

    # ── Filtro de categoría desde contexto ──────────────────────────────
    category: str | None = (
        request.context.get("category") if request.context else None
    )

    # ── Cold-start: populares reales + strategic_priority ───────────────
    if not has_history:
        return _cold_start_pool(session, pool_size, category)

    # ── Cliente con historial: catálogo activo ──────────────────────────
    q = select(Producto).where(Producto.active == True)  # noqa: E712
    if category:
        q = q.where(Producto.category == category)
    candidates = list(session.exec(q).all())

    return candidates


def _cold_start_pool(
    session: Session,
    pool_size: int,
    category: str | None,
) -> list[Producto]:
    """Construye el pool cold-start combinando popularidad real + fallback.

    1. Trae los product_ids más comprados (popularidad real desde purchases).
    2. Carga los objetos Producto correspondientes.
    3. Complementa con productos por strategic_priority para llenar el pool
       y cubrir el caso en que no haya suficientes purchases.
    4. Elimina duplicados, respeta pool_size.
    """
    # ── Paso 1: productos populares reales ──────────────────────────────
    popular_ids = get_popular_product_ids(
        session, limit=pool_size, category=category,
    )

    popular_products: list[Producto] = []
    if popular_ids:
        q = select(Producto).where(
            Producto.product_id.in_(popular_ids),  # type: ignore[union-attr]
            Producto.active == True,  # noqa: E712
        )
        popular_products = list(session.exec(q).all())
        # Ordenar según el orden de popularidad original
        id_order = {pid: idx for idx, pid in enumerate(popular_ids)}
        popular_products.sort(key=lambda p: id_order.get(p.product_id, 999))

    # ── Paso 2: fallback por strategic_priority ─────────────────────────
    q_fallback = select(Producto).where(Producto.active == True)  # noqa: E712
    if category:
        q_fallback = q_fallback.where(Producto.category == category)
    q_fallback = q_fallback.order_by(
        Producto.strategic_priority.desc()  # type: ignore[union-attr]
    ).limit(pool_size)
    strategic_products = list(session.exec(q_fallback).all())

    # ── Paso 3: merge deduplicado, populares primero ────────────────────
    seen: set[str] = set()
    merged: list[Producto] = []

    for p in popular_products:
        if p.product_id not in seen:
            seen.add(p.product_id)
            merged.append(p)

    for p in strategic_products:
        if p.product_id not in seen:
            seen.add(p.product_id)
            merged.append(p)

    return merged[:pool_size]
