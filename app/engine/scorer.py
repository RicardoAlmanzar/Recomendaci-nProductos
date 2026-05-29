from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from app.engine.feedback import FeedbackSignals
from app.engine.formatting import round_score
from app.engine.rules import ScoreSlot, add_margin_boost, add_newness_boost
from app.models import Compra, Cliente, Producto, Regla


def build_recommendations(
	customer: Cliente,
	catalog: Sequence[Producto],
	affinity_rules: Sequence[Regla],
	purchases: Sequence[Compra],
	limit: int,
	popularity_scores: dict[str, float] | None = None,
	feedback_signals: FeedbackSignals | None = None,
):
	if popularity_scores is None:
		popularity_scores = {}
	if feedback_signals is None:
		feedback_signals = FeedbackSignals()
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
		if product.product_id in feedback_signals.excluded_product_ids:
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
					"weight": round_score(rule.weight),
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
				pop_boost = round_score(pop_score * 0.25)  # Max boost = 0.25
				slot.popularity_boost += pop_boost
				slot.score += pop_boost
				slot.reason_codes.add("COLD_START_POPULAR")
			elif slot.score > 0:
				slot.reason_codes.add("COLD_START")

	for slot in score_map.values():
		feedback_adjustment = feedback_signals.adjustment_for(slot.product.product_id)
		if feedback_adjustment == 0:
			continue

		slot.feedback_adjustment += feedback_adjustment
		slot.score += feedback_adjustment
		slot.reason_codes.update(feedback_signals.reason_codes_for(slot.product.product_id))

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
			"score": round_score(slot.score),
			"reason_codes": sorted(slot.reason_codes),
			"explanation": {
				"rule_score": round_score(slot.rule_score),
				"margin_boost": round_score(slot.margin_boost),
				"strategic_boost": round_score(slot.strategic_boost),
				"newness_boost": round_score(slot.newness_boost),
				"popularity_boost": round_score(slot.popularity_boost),
				"feedback_adjustment": round_score(slot.feedback_adjustment),
				"final_score": round_score(slot.score),
				"formula": (
					f"{round_score(slot.rule_score):.4f} + {round_score(slot.margin_boost):.4f}"
					f" + {round_score(slot.strategic_boost):.4f} + {round_score(slot.newness_boost):.4f}"
					f" + {round_score(slot.popularity_boost):.4f} + {round_score(slot.feedback_adjustment):.4f}"
					f" = {round_score(slot.score):.4f}"
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
