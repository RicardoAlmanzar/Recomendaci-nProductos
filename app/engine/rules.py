from __future__ import annotations

from dataclasses import dataclass, field


MAX_MARGIN_REFERENCE = 0.4


@dataclass
class ScoreSlot:
	product: object
	score: float = 0.0
	rule_score: float = 0.0
	margin_boost: float = 0.0
	strategic_boost: float = 0.0
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