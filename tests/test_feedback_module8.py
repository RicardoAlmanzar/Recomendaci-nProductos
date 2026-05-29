import inspect
import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.feedback import FeedbackSignals, get_feedback_signals
from app.engine.ranker import RankingContext, rank
from app.models.event import Event, EventCreate, EventType
from app.routes.events import _validate_recommendation_feedback


class MockProducto:
    def __init__(
        self,
        product_id,
        sku,
        name,
        category,
        active=True,
        margin_pct=0.2,
        strategic_priority=0.5,
    ):
        self.product_id = product_id
        self.sku = sku
        self.name = name
        self.category = category
        self.active = active
        self.margin_pct = margin_pct
        self.strategic_priority = strategic_priority


class MockCliente:
    def __init__(self, customer_id="CUST-FEEDBACK"):
        self.customer_id = customer_id
        self.business_type = "retail"
        self.city = "Santo Domingo"


class MockCompra:
    def __init__(self, product_id):
        self.product_id = product_id


class MockRegla:
    def __init__(self, source_category, target_category, weight=0.8):
        self.source_category = source_category
        self.target_category = target_category
        self.weight = weight
        self.reason_code = "CROSS_SELL"
        self.active = True


class MockResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class MockSession:
    def __init__(self, rows):
        self.rows = rows

    def exec(self, _statement):
        return MockResult(self.rows)


class TestFeedbackEventContract(unittest.TestCase):
    def test_event_type_exists(self):
        self.assertEqual(
            EventType.recommendation_feedback.value,
            "recommendation_feedback",
        )

    def test_feedback_requires_product_id(self):
        payload = EventCreate(
            event_type=EventType.recommendation_feedback,
            entity_id=str(uuid.uuid4()),
            properties={"feedback_type": "hide"},
        )

        with self.assertRaises(HTTPException):
            _validate_recommendation_feedback(payload)

    def test_feedback_requires_known_type(self):
        payload = EventCreate(
            event_type=EventType.recommendation_feedback,
            entity_id=str(uuid.uuid4()),
            properties={"product_id": "P-001", "feedback_type": "maybe"},
        )

        with self.assertRaises(HTTPException):
            _validate_recommendation_feedback(payload)

    def test_feedback_accepts_valid_payload(self):
        payload = EventCreate(
            event_type=EventType.recommendation_feedback,
            entity_id=str(uuid.uuid4()),
            properties={
                "product_id": "P-001",
                "feedback_type": "not_interested",
                "rank_position": 2,
            },
        )

        _validate_recommendation_feedback(payload)


class TestFeedbackSignals(unittest.TestCase):
    def test_latest_feedback_per_product_wins(self):
        now = datetime.utcnow()
        rows = [
            Event(
                event_type=EventType.recommendation_feedback,
                customer_id="CUST-FEEDBACK",
                entity_id="rec-2",
                properties={"product_id": "P-001", "feedback_type": "like"},
                timestamp=now,
            ),
            Event(
                event_type=EventType.recommendation_feedback,
                customer_id="CUST-FEEDBACK",
                entity_id="rec-1",
                properties={"product_id": "P-001", "feedback_type": "hide"},
                timestamp=now - timedelta(minutes=5),
            ),
        ]

        signals = get_feedback_signals(
            customer_id="CUST-FEEDBACK",
            session_id=None,
            session=MockSession(rows),
        )

        self.assertNotIn("P-001", signals.excluded_product_ids)
        self.assertGreater(signals.adjustment_for("P-001"), 0)
        self.assertIn("FEEDBACK_LIKED", signals.reason_codes_for("P-001"))

    def test_hide_excludes_product(self):
        rows = [
            Event(
                event_type=EventType.recommendation_feedback,
                customer_id="CUST-FEEDBACK",
                entity_id="rec-1",
                properties={"product_id": "P-002", "feedback_type": "hide"},
                timestamp=datetime.utcnow(),
            ),
        ]

        signals = get_feedback_signals(
            customer_id="CUST-FEEDBACK",
            session_id=None,
            session=MockSession(rows),
        )

        self.assertIn("P-002", signals.excluded_product_ids)
        self.assertEqual(signals.adjustment_for("P-002"), 0.0)


class TestFeedbackRanking(unittest.TestCase):
    def setUp(self):
        self.products = [
            MockProducto("P-001", "SKU-001", "Caja", "packaging", strategic_priority=0.5),
            MockProducto("P-002", "SKU-002", "Bolsa", "packaging", strategic_priority=0.5),
            MockProducto("P-003", "SKU-003", "Quimico", "cleaning", strategic_priority=0.5),
        ]
        self.customer = MockCliente()
        self.purchases = [MockCompra("P-003")]
        self.rules = [MockRegla("cleaning", "packaging")]

    def test_rank_signature_stays_stable(self):
        sig = inspect.signature(rank)
        self.assertEqual(list(sig.parameters.keys()), ["candidates", "context"])

    def test_hide_feedback_removes_product_from_ranking(self):
        ctx = RankingContext(
            customer=self.customer,
            purchases=self.purchases,
            affinity_rules=self.rules,
            limit=10,
            feedback_signals=FeedbackSignals(excluded_product_ids={"P-001"}),
        )

        result = rank(candidates=self.products, context=ctx)
        result_ids = {item["product_id"] for item in result}

        self.assertNotIn("P-001", result_ids)
        self.assertIn("P-002", result_ids)

    def test_like_feedback_adds_reason_and_boost(self):
        ctx = RankingContext(
            customer=self.customer,
            purchases=self.purchases,
            affinity_rules=self.rules,
            limit=10,
            feedback_signals=FeedbackSignals(
                product_adjustments={"P-002": 0.2},
                reason_codes_by_product={"P-002": {"FEEDBACK_LIKED"}},
            ),
        )

        result = rank(candidates=self.products, context=ctx)
        liked = next(item for item in result if item["product_id"] == "P-002")

        self.assertIn("FEEDBACK_LIKED", liked["reason_codes"])
        self.assertEqual(liked["explanation"]["feedback_adjustment"], 0.2)

    def test_not_interested_feedback_penalizes_product(self):
        ctx = RankingContext(
            customer=self.customer,
            purchases=self.purchases,
            affinity_rules=self.rules,
            limit=10,
            feedback_signals=FeedbackSignals(
                product_adjustments={"P-001": -0.3},
                reason_codes_by_product={"P-001": {"FEEDBACK_NOT_INTERESTED"}},
            ),
        )

        result = rank(candidates=self.products, context=ctx)
        penalized = next(item for item in result if item["product_id"] == "P-001")

        self.assertIn("FEEDBACK_NOT_INTERESTED", penalized["reason_codes"])
        self.assertEqual(penalized["explanation"]["feedback_adjustment"], -0.3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
