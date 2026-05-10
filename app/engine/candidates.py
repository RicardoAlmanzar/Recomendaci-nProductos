"""
Capa de candidatos — Módulo 11.

Responsabilidad: dado un request, devolver los objetos Producto candidatos
que el ranker procesará.  Esta capa NO hace scoring ni excluye compras
previas (eso lo hace el scorer internamente).
"""
from __future__ import annotations

from sqlmodel import Session, select

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
    - Cold-start: si el cliente no tiene compras, retorna los productos
      con mayor strategic_priority (el scorer retornaría vacío sin esto).
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

    # ── Cold-start: top productos por strategic_priority ────────────────
    if not has_history:
        q = select(Producto).where(Producto.active == True)  # noqa: E712
        if category:
            q = q.where(Producto.category == category)
        q = q.order_by(Producto.strategic_priority.desc()).limit(pool_size)  # type: ignore[union-attr]
        return list(session.exec(q).all())

    # ── Cliente con historial: catálogo activo ──────────────────────────
    q = select(Producto).where(Producto.active == True)  # noqa: E712
    if category:
        q = q.where(Producto.category == category)
    candidates = list(session.exec(q).all())

    return candidates
