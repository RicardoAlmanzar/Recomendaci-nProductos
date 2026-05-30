"""
app/services/metrics.py — Módulo 9: Tracking + Cálculo de Métricas.

Funciones:
  register_event()              → side-effect de tracking (Prompt 3, intacto)
  get_summary_counts()          → conteos base para CTR y conversión
  get_ctr_per_item()            → clicks / items_served
  get_ctr_per_response()        → distinct entity_id con click / shown
  get_conversion_rate()         → purchase/add_to_cart con entity_id / shown
  get_top_recommended_products()→ GROUP BY product_id desde properties JSONB
  compute_metrics()             → agregado para /admin/metrics (Prompt 5)

Campos reales usados:
  Event.event_type, Event.entity_id, Event.entity_type,
  Event.properties (JSONB), Event.timestamp, Event.customer_id, Event.session_id
  recommendation_id → entity_id
  product_id        → properties["product_id"] / properties["product_ids"]
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import or_
from sqlmodel import Session, select

from app.models.event import Event, EventType

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# TRACKING (Prompt 3 — no modificar)
# ─────────────────────────────────────────────────────────────────────────────

def register_event(
    session: Session,
    event_type: EventType,
    customer_id: str,
    session_id: str | None = None,
    entity_id: str | None = None,
    entity_type: str | None = None,
    properties: dict[str, Any] | None = None,
) -> None:
    """Persiste un evento de comportamiento en la tabla ``events``.

    Diseñada para ser llamada como side-effect desde endpoints.

    - Usa los campos reales del modelo Event: event_type, customer_id,
      session_id, entity_id, entity_type, properties (JSONB), timestamp.
    - timestamp y event_id son asignados automáticamente por los
      default_factory definidos en Event (ver app/models/event.py).
    - Si falla por cualquier motivo: loguea el error, hace rollback de la
      sesión y retorna sin lanzar excepción.
    """
    try:
        event = Event(
            event_type=event_type,
            customer_id=customer_id,
            session_id=session_id,
            entity_id=entity_id,
            entity_type=entity_type,
            properties=properties,
            schema_version=1,
        )
        session.add(event)
        session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "register_event failed [event_type=%s customer_id=%s entity_id=%s]: %s",
            getattr(event_type, "value", event_type),
            customer_id,
            entity_id,
            exc,
        )
        try:
            session.rollback()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# MÉTRICAS (Prompt 4)
# ─────────────────────────────────────────────────────────────────────────────

def _cutoff(days: int) -> datetime:
    """Retorna datetime UTC de hace `days` días (límite inferior de ventana)."""
    return datetime.utcnow() - timedelta(days=days)


def _extract_product_ids(props: dict) -> list[str]:
    """Extrae product_ids de un evento recommendation_shown.

    Soporta 3 estructuras reales encontradas en producción, en orden
    de prioridad:

      1. properties["product_ids"]  → lista plana ["P-1", "P-2"]
         (formato del backend register_event en recomendaciones.py)
      2. properties["items"]        → lista de dicts [{"product_id": ...}]
         (formato del frontend app.js trackRecommendationShown)
      3. properties["products"]     → ídem, variante futura de seguridad

    Ignora elementos inválidos sin lanzar error.
    Retorna [] si no puede extraer nada.
    """
    # 1. Formato plano: ["P-1", "P-2"]
    product_ids = props.get("product_ids")
    if isinstance(product_ids, list) and product_ids:
        return [
            pid for pid in product_ids
            if isinstance(pid, str) and pid.strip()
        ]

    # 2. Formato estructurado: [{"product_id": "P-1", ...}]
    for key in ("items", "products"):
        items = props.get(key)
        if isinstance(items, list) and items:
            extracted = []
            for item in items:
                if isinstance(item, dict):
                    pid = item.get("product_id")
                    if isinstance(pid, str) and pid.strip():
                        extracted.append(pid)
            if extracted:
                return extracted

    return []


def get_summary_counts(db: Session, days: int = 30) -> dict:
    """Conteos base para todas las métricas derivadas.

    Fórmulas:
      recommendations_served = COUNT(recommendation_shown, timestamp >= cutoff)
      items_served           = SUM(properties["item_count"]) o len(properties["product_ids"])
      clicks                 = COUNT(recommendation_clicked con properties.product_id válido)
      conversions            = COUNT(purchase|add_to_cart con entity_id != null
                                     y entity_type == "recommendation")

    Retorna:
      {
        "total_recommendations_served": int,
        "total_items_served": int,
        "total_clicks": int,
        "total_conversions": int,
      }
    """
    cutoff = _cutoff(days)
    try:
        # ── 1. recommendation_shown ──────────────────────────────────────────
        shown_events = db.exec(
            select(Event)
            .where(Event.event_type == EventType.recommendation_shown)
            .where(Event.timestamp >= cutoff)
        ).all()

        total_recommendations_served = len(shown_events)

        total_items_served = 0
        for ev in shown_events:
            props = ev.properties or {}
            if "item_count" in props:
                total_items_served += int(props["item_count"])
            else:
                # Fallback: contar productos extraídos de cualquier formato
                extracted = _extract_product_ids(props)
                if extracted:
                    total_items_served += len(extracted)

        # ── 2. recommendation_clicked con product_id válido ──────────────────
        clicked_events = db.exec(
            select(Event)
            .where(Event.event_type == EventType.recommendation_clicked)
            .where(Event.timestamp >= cutoff)
        ).all()

        total_clicks = sum(
            1 for ev in clicked_events
            if isinstance((ev.properties or {}).get("product_id"), str)
            and (ev.properties or {}).get("product_id", "").strip()
        )

        # ── 3. purchase / add_to_cart con recommendation_id en entity_id ────
        conversion_events = db.exec(
            select(Event)
            .where(
                or_(
                    Event.event_type == EventType.purchase,
                    Event.event_type == EventType.add_to_cart,
                )
            )
            .where(Event.entity_id.is_not(None))  # type: ignore[union-attr]
            .where(Event.entity_type == "recommendation")
            .where(Event.timestamp >= cutoff)
        ).all()

        total_conversions = len(conversion_events)

    except Exception as exc:
        logger.error("get_summary_counts failed: %s", exc)
        return {
            "total_recommendations_served": 0,
            "total_items_served": 0,
            "total_clicks": 0,
            "total_conversions": 0,
        }

    return {
        "total_recommendations_served": total_recommendations_served,
        "total_items_served": total_items_served,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
    }


def get_ctr_per_item(db: Session, days: int = 30) -> float:
    """CTR por ítem = total_clicks / total_items_served.

    Denominador: total de apariciones de producto en listas servidas
                 (SUM de item_count en eventos recommendation_shown).
    Numerador:   eventos recommendation_clicked con product_id válido.

    Retorna 0.0 si total_items_served == 0 o si falla la query.
    """
    try:
        counts = get_summary_counts(db, days)
        items_served = counts["total_items_served"]
        if items_served == 0:
            return 0.0
        return round(counts["total_clicks"] / items_served, 4)
    except Exception as exc:
        logger.error("get_ctr_per_item failed: %s", exc)
        return 0.0


def get_ctr_per_response(db: Session, days: int = 30) -> float:
    """CTR por respuesta = distinct entity_id con click / total recommendation_shown.

    Denominador: COUNT de eventos recommendation_shown en la ventana.
    Numerador:   COUNT DISTINCT de entity_id en eventos recommendation_clicked
                 (cada recommendation_id único que recibió al menos un click).

    Retorna 0.0 si no hay recommendation_shown o si falla la query.
    """
    cutoff = _cutoff(days)
    try:
        shown_count = len(
            db.exec(
                select(Event)
                .where(Event.event_type == EventType.recommendation_shown)
                .where(Event.timestamp >= cutoff)
            ).all()
        )
        if shown_count == 0:
            return 0.0

        clicked_events = db.exec(
            select(Event)
            .where(Event.event_type == EventType.recommendation_clicked)
            .where(Event.entity_id.is_not(None))  # type: ignore[union-attr]
            .where(Event.timestamp >= cutoff)
        ).all()

        unique_rec_ids = {ev.entity_id for ev in clicked_events}
        return round(len(unique_rec_ids) / shown_count, 4)

    except Exception as exc:
        logger.error("get_ctr_per_response failed: %s", exc)
        return 0.0


def get_conversion_rate(db: Session, days: int = 30) -> dict:
    """Conversión directa = purchase/add_to_cart con entity_id / recommendation_shown.

    Solo cuenta conversiones donde entity_id != null Y entity_type == "recommendation"
    (indica que la compra fue atribuida a una recomendación específica).
    La tabla Compra NO se usa porque no tiene recommendation_id ni session_id.

    Retorna:
      {"rate": float, "type": "direct", "numerator": int, "denominator": int}
    """
    try:
        counts = get_summary_counts(db, days)
        numerator = counts["total_conversions"]
        denominator = counts["total_recommendations_served"]
        rate = round(numerator / denominator, 4) if denominator > 0 else 0.0
        return {
            "rate": rate,
            "type": "direct",
            "numerator": numerator,
            "denominator": denominator,
        }
    except Exception as exc:
        logger.error("get_conversion_rate failed: %s", exc)
        return {"rate": 0.0, "type": "direct", "numerator": 0, "denominator": 0}


def get_top_recommended_products(
    db: Session,
    limit: int = 10,
    days: int = 30,
) -> list[dict]:
    """Top productos por frecuencia de aparición en listas servidas.

    recommendation_count: COUNT de veces que product_id apareció en
      eventos recommendation_shown, extraído via _extract_product_ids()
      (soporta product_ids, items, y products).
    click_count: COUNT de eventos recommendation_clicked donde
      properties["product_id"] == product_id.
    ctr: click_count / recommendation_count por producto.

    Ordenado por recommendation_count DESC. Retorna [] si no hay datos.
    """
    cutoff = _cutoff(days)
    try:
        # ── Extraer product_ids de eventos shown ─────────────────────────────
        shown_events = db.exec(
            select(Event)
            .where(Event.event_type == EventType.recommendation_shown)
            .where(Event.timestamp >= cutoff)
        ).all()

        rec_count: dict[str, int] = {}
        for ev in shown_events:
            props = ev.properties or {}
            for pid in _extract_product_ids(props):
                rec_count[pid] = rec_count.get(pid, 0) + 1

        if not rec_count:
            return []

        # ── Contar clicks por product_id ─────────────────────────────────────
        clicked_events = db.exec(
            select(Event)
            .where(Event.event_type == EventType.recommendation_clicked)
            .where(Event.timestamp >= cutoff)
        ).all()

        click_count: dict[str, int] = {}
        for ev in clicked_events:
            props = ev.properties or {}
            pid = props.get("product_id")
            if isinstance(pid, str) and pid.strip():
                click_count[pid] = click_count.get(pid, 0) + 1

        # ── Construir resultado ordenado ─────────────────────────────────────
        top = sorted(rec_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [
            {
                "product_id": pid,
                "recommendation_count": count,
                "click_count": click_count.get(pid, 0),
                "ctr": round(click_count.get(pid, 0) / count, 4) if count > 0 else 0.0,
            }
            for pid, count in top
        ]

    except Exception as exc:
        logger.error("get_top_recommended_products failed: %s", exc)
        return []


def compute_metrics(
    db: Session,
    window_days: int = 30,
    top_n: int = 10,
) -> dict:
    """Agregado principal para el endpoint GET /admin/metrics (Prompt 5).

    Llama a todas las funciones de métricas y consolida el resultado.
    En caso de fallo general retorna un dict seguro con ceros.

    Response shape (ver Decisión 5 del documento de diseño):
      window_days, generated_at, recommendations_served, items_served,
      clicks, ctr_item, ctr_response, conversions_direct,
      conversion_rate_direct, top_recommended_products
    """
    try:
        counts = get_summary_counts(db, window_days)
        ctr_item = get_ctr_per_item(db, window_days)
        ctr_response = get_ctr_per_response(db, window_days)
        conversion_info = get_conversion_rate(db, window_days)
        top_products = get_top_recommended_products(db, top_n, window_days)

        return {
            "window_days": window_days,
            "generated_at": datetime.utcnow().isoformat(),
            "recommendations_served": counts["total_recommendations_served"],
            "items_served": counts["total_items_served"],
            "clicks": counts["total_clicks"],
            "ctr_item": ctr_item,
            "ctr_response": ctr_response,
            "conversions_direct": conversion_info["numerator"],
            "conversion_rate_direct": conversion_info["rate"],
            "top_recommended_products": top_products,
        }
    except Exception as exc:
        logger.error("compute_metrics failed: %s", exc)
        return {
            "window_days": window_days,
            "generated_at": datetime.utcnow().isoformat(),
            "recommendations_served": 0,
            "items_served": 0,
            "clicks": 0,
            "ctr_item": 0.0,
            "ctr_response": 0.0,
            "conversions_direct": 0,
            "conversion_rate_direct": 0.0,
            "top_recommended_products": [],
        }
