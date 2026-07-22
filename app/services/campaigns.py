"""Gestión de campañas y ofertas comerciales — Módulo 4."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from app.models.campana import Campana
from app.models.oferta import Oferta


def serialize_campaign(campaign: Campana) -> dict:
    return {
        "campaign_id": campaign.campaign_id,
        "name": campaign.name,
        "channel": campaign.channel,
        "active": campaign.active,
        "starts_at": campaign.starts_at.isoformat() if campaign.starts_at else None,
        "ends_at": campaign.ends_at.isoformat() if campaign.ends_at else None,
    }


def serialize_offer(offer: Oferta) -> dict:
    return {
        "offer_id": offer.offer_id,
        "campaign_id": offer.campaign_id,
        "product_id": offer.product_id,
        "extra_score": offer.extra_score,
        "active": offer.active,
    }


def list_campaigns(session: Session) -> list[dict]:
    campaigns = session.exec(select(Campana).order_by(Campana.campaign_id)).all()
    return [serialize_campaign(campaign) for campaign in campaigns]


def create_campaign(session: Session, payload: dict) -> dict:
    required = {"name", "channel"}
    missing = sorted(required - set(payload.keys()))
    if missing:
        raise ValueError(f"Faltan campos: {missing}")

    campaign = Campana(
        name=str(payload["name"]),
        channel=str(payload["channel"]),
        active=bool(payload.get("active", True)),
        starts_at=payload.get("starts_at"),
        ends_at=payload.get("ends_at"),
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return serialize_campaign(campaign)


def list_offers(session: Session, campaign_id: int | None = None) -> list[dict]:
    query = select(Oferta).order_by(Oferta.offer_id)
    if campaign_id is not None:
        query = query.where(Oferta.campaign_id == campaign_id)
    offers = session.exec(query).all()
    return [serialize_offer(offer) for offer in offers]


def create_offer(session: Session, payload: dict) -> dict:
    required = {"campaign_id", "product_id", "extra_score"}
    missing = sorted(required - set(payload.keys()))
    if missing:
        raise ValueError(f"Faltan campos: {missing}")

    campaign = session.get(Campana, int(payload["campaign_id"]))
    if campaign is None:
        raise ValueError("Campaña no encontrada")

    offer = Oferta(
        campaign_id=int(payload["campaign_id"]),
        product_id=str(payload["product_id"]),
        extra_score=float(payload["extra_score"]),
        active=bool(payload.get("active", True)),
    )
    session.add(offer)
    session.commit()
    session.refresh(offer)
    return serialize_offer(offer)


def get_active_offer_scores(
    session: Session,
    channel: str | None = None,
    now: datetime | None = None,
) -> dict[str, float]:
    """Devuelve extra_score por product_id para campañas/ofertas activas."""
    if now is None:
        now = datetime.utcnow()

    campaigns = session.exec(select(Campana).where(Campana.active.is_(True))).all()
    active_campaign_ids: list[int] = []
    for campaign in campaigns:
        if channel and campaign.channel != channel:
            continue
        if campaign.starts_at and campaign.starts_at > now:
            continue
        if campaign.ends_at and campaign.ends_at < now:
            continue
        if campaign.campaign_id is not None:
            active_campaign_ids.append(campaign.campaign_id)

    if not active_campaign_ids:
        return {}

    offers = session.exec(
        select(Oferta).where(
            Oferta.active.is_(True),
            Oferta.campaign_id.in_(active_campaign_ids),
        )
    ).all()

    scores: dict[str, float] = {}
    for offer in offers:
        scores[offer.product_id] = scores.get(offer.product_id, 0.0) + float(offer.extra_score)
    return scores
