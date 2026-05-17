from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from app.engine.rules import ScoreSlot, add_margin_boost, add_newness_boost
from app.models import Compra, Cliente, Producto, Regla


def build_recommendations(
	customer: Cliente,
	catalog: Sequence[Producto],
	affinity_rules: Sequence[Regla],
	purchases: Sequence[Compra],
	limit: int,
	popularity_scores: dict[str, float] | None = None,
):
	if popularity_scores is None:
		popularity_scores = {}
	purchased_product_ids = {purchase.product_id for purchase in purchases}
	product_category_by_id = {product.product_id: product.category for product in catalog}
	purchased_categories = {
		product_category_by_id[product_id]
		for product_id in purchased_product_ids
		if product_id in product_category_by_id
	}

	# ── Detectar cold-start — Módulo 7 ──────────────────────────────────
	is_cold_start = len(purchased_product_ids) == 0

	score_map: dict[str, ScoreSlot] = {}

	for product in catalog:
		if not product.active or product.product_id in purchased_product_ids:
			continue

		score_map[product.product_id] = ScoreSlot(product=product)

	for rule in affinity_rules:
		if not rule.active or rule.source_category not in purchased_categories:
			continue

		for slot in score_map.values():
			if slot.product.category != rule.target_category:
				continue

			slot.score += float(rule.weight)
			slot.rule_score += float(rule.weight)
			slot.reason_codes.add(rule.reason_code)
			slot.matched_rules.append(
				{
					"reason_code": rule.reason_code,
					"weight": round(float(rule.weight), 4),
					"source_category": rule.source_category,
					"target_category": rule.target_category,
				}
			)

	for slot in score_map.values():
		add_margin_boost(slot)

	# ── Boost por novedad — Módulo 7 ────────────────────────────────────
	now = datetime.utcnow()
	for slot in score_map.values():
		add_newness_boost(slot, now=now)

	# ── Cold-start: popularidad como fallback — Módulo 7 ────────────────
	if is_cold_start:
		for slot in score_map.values():
			pop_score = popularity_scores.get(slot.product.product_id, 0.0)
			if pop_score > 0:
				pop_boost = round(pop_score * 0.25, 4)  # Max boost = 0.25
				slot.popularity_boost += pop_boost
				slot.score += pop_boost
				slot.reason_codes.add("COLD_START_POPULAR")
			elif slot.score > 0:
				slot.reason_codes.add("COLD_START")

	recommendations = sorted(
		[slot for slot in score_map.values() if slot.score > 0],
		key=lambda slot: slot.score,
		reverse=True,
	)[:limit]

	return [
		{
			"product_id": slot.product.product_id,
			"sku": slot.product.sku,
			"name": slot.product.name,
			"score": round(slot.score, 4),
			"reason_codes": sorted(slot.reason_codes),
			"explanation": {
				"rule_score": round(slot.rule_score, 4),
				"margin_boost": round(slot.margin_boost, 4),
				"strategic_boost": round(slot.strategic_boost, 4),
				"newness_boost": round(slot.newness_boost, 4),
				"popularity_boost": round(slot.popularity_boost, 4),
				"final_score": round(slot.score, 4),
				"formula": (
					f"{round(slot.rule_score, 4)} + {round(slot.margin_boost, 4)}"
					f" + {round(slot.strategic_boost, 4)} + {round(slot.newness_boost, 4)}"
					f" + {round(slot.popularity_boost, 4)} = {round(slot.score, 4)}"
				),
				"matched_rules": slot.matched_rules,
			},
		}
		for slot in recommendations
	]


def build_recommendation_payload(customer_id: str, recommendations: list[dict]):
	return {
		"customer_id": customer_id,
		"generated_at": datetime.utcnow().isoformat() + "Z",
		"recommendations": recommendations,
	}