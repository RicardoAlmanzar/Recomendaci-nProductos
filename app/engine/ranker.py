"""
Capa de ranking — Módulo 5.

Responsabilidad: dado el pool de candidatos y un contexto de ranking,
aplicar el algoritmo de scoring y devolver la lista ordenada.

Contrato público:
    rank(candidates, context) -> list[dict[str, Any]]

Punto de sustitución ML / Learning-to-Rank:
    Cuando existan suficientes datos de interacción (~50k-100k eventos),
    se puede reemplazar la implementación interna de rank() por un modelo
    LTR sin modificar el endpoint ni el generador de candidatos.
    Solo cambia el cuerpo de rank(); la firma se mantiene igual.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Optional

from app.engine.scorer import build_recommendations
from app.models.cliente import Cliente
from app.models.compra import Compra
from app.models.producto import Producto
from app.models.regla import Regla


# ---------------------------------------------------------------------------
# Contrato de contexto para el ranker
# ---------------------------------------------------------------------------

@dataclass
class RankingContext:
    """Agrupa todo el contexto que el ranker necesita para ordenar candidatos.

    Diseñado para ser el único argumento de contexto de rank(), de modo que
    agregar señales futuras (hora del día, dispositivo, canal, feedback)
    solo requiere añadir campos aquí sin cambiar la firma pública.
    """
    customer: Cliente
    purchases: Sequence[Compra]
    affinity_rules: Sequence[Regla]
    limit: int = 10

    # Metadatos del request — útiles para estrategias futuras de ranking
    # (ej. ponderar distinto en homepage vs cart, o por slot).
    page_type: Optional[str] = None
    slot: Optional[str] = None
    session_id: Optional[str] = None
    request_context: Optional[dict[str, Any]] = field(default=None)


# ---------------------------------------------------------------------------
# Función pública de ranking
# ---------------------------------------------------------------------------

def rank(
    candidates: Sequence[Producto],
    context: RankingContext,
) -> list[dict[str, Any]]:
    """Ordena los candidatos usando el motor de scoring existente.

    Recibe:
        candidates: productos candidatos generados por get_candidates().
        context:    RankingContext con cliente, historial, reglas y límite.

    Retorna:
        Lista de dicts ordenada por score descendente, con las keys:
        product_id, sku, name, score, reason_codes, explanation.

    --- Punto de sustitución futuro ---
    Para migrar a Learning-to-Rank:
    1. Mantener esta misma firma: rank(candidates, context) -> list[dict].
    2. Reemplazar la llamada a build_recommendations() por el modelo LTR.
    3. Asegurar que la salida conserve las mismas keys del dict.
    4. El endpoint y el generador de candidatos no necesitan cambios.
    """
    return build_recommendations(
        customer=context.customer,
        catalog=candidates,
        affinity_rules=context.affinity_rules,
        purchases=context.purchases,
        limit=context.limit,
    )
