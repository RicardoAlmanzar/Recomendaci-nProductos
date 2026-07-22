"""Servicios administrativos — reglas de afinidad y estado del sistema."""

from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import func, text
from sqlmodel import Session, select

from app.engine.cache import cache
from app.models import Cliente, Producto, Regla
from app.models.event import Event

ALGO_VERSION = os.getenv("ALGO_VERSION", "rules_v1")
SERVICE_VERSION = "0.2.0"


def serialize_rule(rule: Regla) -> dict:
    return {
        "rule_id": rule.rule_id,
        "source_category": rule.source_category,
        "target_category": rule.target_category,
        "weight": rule.weight,
        "reason_code": rule.reason_code,
        "active": rule.active,
    }


def list_rules(session: Session) -> list[dict]:
    rules = session.exec(select(Regla).order_by(Regla.rule_id)).all()
    return [serialize_rule(rule) for rule in rules]


def get_rule(session: Session, rule_id: int) -> Regla | None:
    return session.get(Regla, rule_id)


def create_rule(session: Session, payload: dict) -> dict:
    required = {"source_category", "target_category", "weight", "reason_code"}
    missing = sorted(required - set(payload.keys()))
    if missing:
        raise ValueError(f"Faltan campos: {missing}")

    rule = Regla(
        source_category=str(payload["source_category"]),
        target_category=str(payload["target_category"]),
        weight=float(payload["weight"]),
        reason_code=str(payload["reason_code"]),
        active=bool(payload.get("active", True)),
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return serialize_rule(rule)


def update_rule(session: Session, rule_id: int, payload: dict) -> Regla | None:
    rule = session.get(Regla, rule_id)
    if rule is None:
        return None

    updatable = {"source_category", "target_category", "weight", "reason_code", "active"}
    for field in updatable:
        if field in payload:
            value = payload[field]
            if field in {"source_category", "target_category", "reason_code"}:
                value = str(value)
            elif field == "weight":
                value = float(value)
            elif field == "active":
                value = bool(value)
            setattr(rule, field, value)

    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def get_system_status(session: Session) -> dict:
    """Resumen operativo del motor para el panel administrativo."""
    db_ok = True
    db_error: str | None = None
    try:
        session.exec(text("SELECT 1")).one()
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    total_rules = session.exec(select(func.count()).select_from(Regla)).one()
    active_rules = session.exec(
        select(func.count()).select_from(Regla).where(Regla.active.is_(True))
    ).one()
    total_products = session.exec(select(func.count()).select_from(Producto)).one()
    active_products = session.exec(
        select(func.count()).select_from(Producto).where(Producto.active.is_(True))
    ).one()
    total_customers = session.exec(select(func.count()).select_from(Cliente)).one()
    total_events = session.exec(select(func.count()).select_from(Event)).one()

    return {
        "status": "ok" if db_ok else "degraded",
        "generated_at": datetime.utcnow().isoformat(),
        "service": {
            "name": "recommendation-engine",
            "version": SERVICE_VERSION,
            "algo_version": ALGO_VERSION,
        },
        "database": {
            "connected": db_ok,
            "error": db_error,
        },
        "cache": {
            "entries": len(cache._store),
            "ttl_seconds": cache.ttl,
        },
        "counts": {
            "rules_total": total_rules,
            "rules_active": active_rules,
            "products_total": total_products,
            "products_active": active_products,
            "customers": total_customers,
            "events": total_events,
        },
    }
