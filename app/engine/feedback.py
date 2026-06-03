from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import or_
from sqlmodel import Session, select

from app.engine.formatting import round_score
from app.models.event import Event, EventType


LIKE_BOOST = 0.2
NOT_INTERESTED_PENALTY = -0.3
DISLIKE_PENALTY = -0.35

_REASON_BY_TYPE = {
    "like": "FEEDBACK_LIKED",
    "hide": "FEEDBACK_HIDDEN",
    "not_interested": "FEEDBACK_NOT_INTERESTED",
    "dislike": "FEEDBACK_DISLIKED",
}
_ADJUSTMENT_BY_TYPE = {
    "like": LIKE_BOOST,
    "not_interested": NOT_INTERESTED_PENALTY,
    "dislike": DISLIKE_PENALTY,
}


@dataclass
class FeedbackSignals:
    excluded_product_ids: set[str] = field(default_factory=set)
    product_adjustments: dict[str, float] = field(default_factory=dict)
    reason_codes_by_product: dict[str, set[str]] = field(default_factory=dict)

    def adjustment_for(self, product_id: str) -> float:
        return self.product_adjustments.get(product_id, 0.0)

    def reason_codes_for(self, product_id: str) -> set[str]:
        return self.reason_codes_by_product.get(product_id, set())


def get_feedback_signals(
    customer_id: str,
    session_id: str | None,
    session: Session,
    limit: int = 500,
) -> FeedbackSignals:
    """Resume feedback explicito reciente para usarlo en ranking.

    La regla es intencionalmente simple: para cada producto gana el feedback
    mas reciente. Esto evita sumar likes/dislikes repetidos y hace que una
    decision nueva del usuario reemplace una anterior.
    """
    query = select(Event).where(Event.event_type == EventType.recommendation_feedback)
    if session_id:
        query = query.where(
            or_(Event.customer_id == customer_id, Event.session_id == session_id)
        )
    else:
        query = query.where(Event.customer_id == customer_id)

    query = query.order_by(Event.timestamp.desc()).limit(limit)  # type: ignore[union-attr]

    signals = FeedbackSignals()
    seen_products: set[str] = set()
    for event in session.exec(query).all():
        properties = event.properties or {}
        product_id = properties.get("product_id")
        feedback_type = properties.get("feedback_type")

        if not isinstance(product_id, str) or product_id in seen_products:
            continue
        if feedback_type not in _REASON_BY_TYPE:
            continue

        seen_products.add(product_id)
        reason_code = _REASON_BY_TYPE[feedback_type]
        signals.reason_codes_by_product.setdefault(product_id, set()).add(reason_code)

        if feedback_type == "hide":
            signals.excluded_product_ids.add(product_id)
            continue

        signals.product_adjustments[product_id] = round_score(
            _ADJUSTMENT_BY_TYPE.get(feedback_type, 0.0)
        )

    return signals
