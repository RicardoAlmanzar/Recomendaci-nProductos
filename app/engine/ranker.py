"""
Capa de ranking — Módulo 11.

Responsabilidad: dado el pool de candidatos, aplicar el algoritmo de
scoring y devolver la lista ordenada limitada a `limit` items.

Punto de sustitución ML: cuando se migre a un modelo, solo cambia la
implementación interna de rank(), sin tocar el endpoint.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.engine.scorer import build_recommendations
from app.models.cliente import Cliente
from app.models.compra import Compra
from app.models.producto import Producto
from app.models.regla import Regla


def rank(
    candidates: Sequence[Producto],
    customer: Cliente,
    affinity_rules: Sequence[Regla],
    purchases: Sequence[Compra],
    limit: int,
) -> list[dict[str, Any]]:
    """
    Ordena los candidatos usando el motor de scoring existente.

    Retorna la lista de dicts que genera build_recommendations()
    (con product_id, sku, name, score, reason_codes, explanation).
    """
    return build_recommendations(
        customer=customer,
        catalog=candidates,
        affinity_rules=affinity_rules,
        purchases=purchases,
        limit=limit,
    )
