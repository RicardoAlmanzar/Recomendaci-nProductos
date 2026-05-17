from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


MAX_MARGIN_REFERENCE = 0.4

# ── Módulo 7: configuración de boost por novedad ────────────────────────
NEWNESS_WINDOW_DAYS = 30
NEWNESS_MAX_BOOST = 0.15  # Menor que una regla de afinidad fuerte (~0.8)


@dataclass
class ScoreSlot:
	product: object
	score: float = 0.0
	rule_score: float = 0.0
	margin_boost: float = 0.0
	strategic_boost: float = 0.0
	newness_boost: float = 0.0
	popularity_boost: float = 0.0
	reason_codes: set[str] = field(default_factory=set)
	matched_rules: list[dict] = field(default_factory=list)


def add_margin_boost(slot: ScoreSlot) -> None:
	margin_boost = min(getattr(slot.product, "margin_pct", 0) / MAX_MARGIN_REFERENCE, 1) * 0.2
	strategic_boost = getattr(slot.product, "strategic_priority", 0) * 0.25

	slot.margin_boost += margin_boost
	slot.strategic_boost += strategic_boost
	slot.score += margin_boost + strategic_boost

	if getattr(slot.product, "margin_pct", 0) >= 0.3:
		slot.reason_codes.add("HIGH_MARGIN")

	if getattr(slot.product, "strategic_priority", 0) >= 0.8:
		slot.reason_codes.add("STRATEGIC_PRIORITY")


def add_newness_boost(
	slot: ScoreSlot,
	now: datetime | None = None,
	window_days: int = NEWNESS_WINDOW_DAYS,
) -> None:
	"""Aplica un boost temporal a productos recientes — Módulo 7.

	Si el producto fue creado dentro de los últimos `window_days` días,
	se le suma un boost decreciente linealmente (más fresco = más boost).
	El boost máximo (0.15) es menor que una regla de afinidad fuerte (0.8–0.9)
	para que no domine el ranking, solo empuje productos nuevos.
	"""
	created_at = getattr(slot.product, "created_at", None)
	if created_at is None:
		return

	if now is None:
		now = datetime.utcnow()

	# Normalizar a naive para comparación segura (PostgreSQL puede devolver aware)
	if getattr(created_at, "tzinfo", None) is not None:
		created_at = created_at.replace(tzinfo=None)
	if getattr(now, "tzinfo", None) is not None:
		now = now.replace(tzinfo=None)

	age_days = max((now - created_at).days, 0)

	if age_days <= window_days:
		freshness = 1.0 - (age_days / window_days)
		boost = round(freshness * NEWNESS_MAX_BOOST, 4)
		slot.newness_boost += boost
		slot.score += boost
		slot.reason_codes.add("NEW_PRODUCT")