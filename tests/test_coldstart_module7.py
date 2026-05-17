"""
Tests del Módulo 7: Cold-start.

Verifica:
- Cliente sin compras recibe recomendaciones (no lista vacía).
- Cliente sin compras recibe reason_code COLD_START.
- Producto reciente recibe reason_code NEW_PRODUCT.
- Producto viejo NO recibe NEW_PRODUCT.
- Newness boost no domina el ranking sobre afinidad.
- Endpoint /recommendations sigue respondiendo 200.
- rank(candidates, context) firma intacta.
- candidates.py no fue modificado.
"""
import inspect
import json
import os
import sys
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.ranker import RankingContext, rank
from app.engine.rules import ScoreSlot, add_newness_boost, NEWNESS_WINDOW_DAYS
from app.engine.candidates import get_candidates, _cold_start_pool
from app.engine.popularity import get_popularity_scores, get_popular_product_ids


BASE = "http://127.0.0.1:8010"


def http(method: str, path: str, body=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# ---------------------------------------------------------------------------
# Mocks mínimos
# ---------------------------------------------------------------------------

class MockProducto:
    def __init__(self, product_id, sku, name, category, active=True,
                 margin_pct=0.2, strategic_priority=0.5, created_at=None):
        self.product_id = product_id
        self.sku = sku
        self.name = name
        self.category = category
        self.active = active
        self.margin_pct = margin_pct
        self.strategic_priority = strategic_priority
        self.created_at = created_at or datetime.utcnow()


class MockCliente:
    def __init__(self, customer_id="CUST-COLD", business_type="retail",
                 city="Santo Domingo"):
        self.customer_id = customer_id
        self.business_type = business_type
        self.city = city


class MockCompra:
    def __init__(self, product_id):
        self.product_id = product_id


class MockRegla:
    def __init__(self, source_category, target_category, weight=0.8,
                 reason_code="CROSS_SELL_RULE", active=True):
        self.source_category = source_category
        self.target_category = target_category
        self.weight = weight
        self.reason_code = reason_code
        self.active = active


# ---------------------------------------------------------------------------
# Tests unitarios: add_newness_boost
# ---------------------------------------------------------------------------

class TestNewnessBoost(unittest.TestCase):

    def test_recent_product_gets_new_product_code(self):
        product = MockProducto("P-NEW", "SKU-NEW", "Nuevo", "packaging",
                               created_at=datetime.utcnow())
        slot = ScoreSlot(product=product)
        add_newness_boost(slot)
        self.assertIn("NEW_PRODUCT", slot.reason_codes)
        self.assertGreater(slot.newness_boost, 0)

    def test_old_product_no_new_product_code(self):
        old_date = datetime.utcnow() - timedelta(days=365)
        product = MockProducto("P-OLD", "SKU-OLD", "Viejo", "packaging",
                               created_at=old_date)
        slot = ScoreSlot(product=product)
        add_newness_boost(slot)
        self.assertNotIn("NEW_PRODUCT", slot.reason_codes)
        self.assertEqual(slot.newness_boost, 0.0)

    def test_boost_decays_over_time(self):
        now = datetime.utcnow()
        product_fresh = MockProducto("P-1", "S-1", "Fresco", "pkg",
                                     created_at=now)
        product_aging = MockProducto("P-2", "S-2", "Envejeciendo", "pkg",
                                     created_at=now - timedelta(days=20))

        slot_fresh = ScoreSlot(product=product_fresh)
        slot_aging = ScoreSlot(product=product_aging)

        add_newness_boost(slot_fresh, now=now)
        add_newness_boost(slot_aging, now=now)

        self.assertGreater(slot_fresh.newness_boost, slot_aging.newness_boost,
                           "Producto más fresco debe tener mayor boost")

    def test_boost_max_is_controlled(self):
        product = MockProducto("P-MAX", "S-MAX", "Max", "pkg",
                               created_at=datetime.utcnow())
        slot = ScoreSlot(product=product)
        add_newness_boost(slot)
        self.assertLessEqual(slot.newness_boost, 0.15,
                             "Newness boost no debe exceder 0.15")

    def test_product_without_created_at_no_crash(self):
        product = MockProducto("P-NONE", "S-NONE", "Sin fecha", "pkg")
        product.created_at = None
        slot = ScoreSlot(product=product)
        add_newness_boost(slot)  # No debe lanzar excepción
        self.assertEqual(slot.newness_boost, 0.0)


# ---------------------------------------------------------------------------
# Tests unitarios: Cold-start de usuario
# ---------------------------------------------------------------------------

class TestColdStartUser(unittest.TestCase):

    def setUp(self):
        self.products = [
            MockProducto("P-001", "SKU-001", "Caja", "packaging",
                         margin_pct=0.35, strategic_priority=0.9),
            MockProducto("P-002", "SKU-002", "Bolsa", "packaging",
                         margin_pct=0.15, strategic_priority=0.3),
            MockProducto("P-003", "SKU-003", "Etiqueta", "labels",
                         margin_pct=0.31, strategic_priority=0.85),
        ]
        self.rules = [
            MockRegla("packaging", "labels", weight=0.9),
        ]

    def test_cold_start_returns_recommendations(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],            # Sin compras = cold-start
            affinity_rules=self.rules,
            limit=10,
        )
        result = rank(candidates=self.products, context=ctx)
        self.assertGreater(len(result), 0,
                           "Cold-start no debe retornar lista vacía")

    def test_cold_start_has_reason_code(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=self.rules,
            limit=10,
        )
        result = rank(candidates=self.products, context=ctx)
        all_codes = set()
        for item in result:
            all_codes.update(item["reason_codes"])
        self.assertIn("COLD_START", all_codes,
                       "Cold-start debe incluir reason_code COLD_START")

    def test_cold_start_auto_detected_in_context(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=5,
        )
        self.assertTrue(ctx.is_cold_start,
                        "RankingContext debe auto-detectar cold-start")

    def test_non_cold_start_no_cold_start_code(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[MockCompra("P-001")],
            affinity_rules=self.rules,
            limit=10,
        )
        self.assertFalse(ctx.is_cold_start)
        result = rank(candidates=self.products, context=ctx)
        for item in result:
            self.assertNotIn("COLD_START", item["reason_codes"])

    def test_newness_boost_does_not_dominate_affinity(self):
        """Un producto con regla de afinidad fuerte debe rankear
        más alto que un producto nuevo sin afinidad."""
        ctx_with_history = RankingContext(
            customer=MockCliente(),
            purchases=[MockCompra("P-001")],  # Compró packaging
            affinity_rules=self.rules,         # packaging -> labels (0.9)
            limit=10,
        )
        result = rank(candidates=self.products, context=ctx_with_history)
        if len(result) >= 2:
            # Etiqueta (labels) con afinidad debe rankear alto
            top_item = result[0]
            self.assertIn("CROSS_SELL_RULE", top_item["reason_codes"],
                          "Afinidad debe dominar sobre newness boost")

    def test_cold_start_popular_reason_code(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=10,
            popularity_scores={"P-001": 1.0, "P-002": 0.5}
        )
        result = rank(candidates=self.products, context=ctx)
        
        p1_result = next(i for i in result if i["product_id"] == "P-001")
        self.assertIn("COLD_START_POPULAR", p1_result["reason_codes"])
        
        p3_result = next(i for i in result if i["product_id"] == "P-003")
        self.assertNotIn("COLD_START_POPULAR", p3_result["reason_codes"])
        self.assertIn("COLD_START", p3_result["reason_codes"])

    def test_cold_start_popularity_boost_applied(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=10,
            popularity_scores={"P-002": 1.0}
        )
        result = rank(candidates=self.products, context=ctx)
        p2_result = next(i for i in result if i["product_id"] == "P-002")
        self.assertGreater(p2_result["explanation"]["popularity_boost"], 0.0)

    def test_history_user_ignores_popularity_boost(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[MockCompra("P-001")],
            affinity_rules=[],
            limit=10,
            popularity_scores={"P-002": 1.0}
        )
        result = rank(candidates=self.products, context=ctx)
        p2_result = next(i for i in result if i["product_id"] == "P-002")
        self.assertEqual(p2_result["explanation"]["popularity_boost"], 0.0)
        self.assertNotIn("COLD_START_POPULAR", p2_result["reason_codes"])

class MockSessionResult:
    def __init__(self, data):
        self.data = data
    def all(self):
        return self.data

class MockSessionPop:
    def __init__(self, data):
        self.data = data
    def exec(self, stmt):
        return MockSessionResult(self.data)

class TestPopularityScores(unittest.TestCase):
    def test_get_popularity_scores_normalized(self):
        session = MockSessionPop([("P1", 10), ("P2", 5), ("P3", 0)])
        scores = get_popularity_scores(session)
        self.assertEqual(scores.get("P1"), 1.0)
        self.assertEqual(scores.get("P2"), 0.5)
        self.assertEqual(scores.get("P3"), 0.0)


# ---------------------------------------------------------------------------
# Tests: cold-start pool con popularidad real
# ---------------------------------------------------------------------------

class TestColdStartPool(unittest.TestCase):

    def test_popular_product_with_low_priority_enters_pool_via_ranking(self):
        """Un producto popular (alta frecuencia de compra) con baja
        strategic_priority debe poder recibir COLD_START_POPULAR
        cuando el scorer lo procesa."""
        # Producto "popular" con strategic_priority bajísima
        low_prio_popular = MockProducto(
            "P-LOW", "SKU-LOW", "Popular bajo prio", "packaging",
            margin_pct=0.1, strategic_priority=0.1,
        )
        other = MockProducto(
            "P-HIGH", "SKU-HIGH", "Alto prio", "labels",
            margin_pct=0.3, strategic_priority=0.9,
        )
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=10,
            popularity_scores={"P-LOW": 1.0},  # P-LOW es el más popular
        )
        result = rank(candidates=[low_prio_popular, other], context=ctx)
        p_low = next(i for i in result if i["product_id"] == "P-LOW")
        self.assertIn("COLD_START_POPULAR", p_low["reason_codes"],
                      "Producto popular debe recibir COLD_START_POPULAR")
        self.assertGreater(p_low["explanation"]["popularity_boost"], 0.0)

    def test_no_purchases_falls_back_to_strategic_priority(self):
        """Si no hay purchases, cold-start no devuelve lista vacía."""
        products = [
            MockProducto("P-A", "S-A", "A", "pkg",
                         margin_pct=0.3, strategic_priority=0.8),
        ]
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=5,
            popularity_scores={},  # vacío = sin data
        )
        result = rank(candidates=products, context=ctx)
        self.assertGreater(len(result), 0, "No debe devolver lista vacía")
        all_codes = set()
        for item in result:
            all_codes.update(item["reason_codes"])
        self.assertIn("COLD_START", all_codes,
                      "Sin popularity debe caer a COLD_START")

    def test_get_popular_product_ids_exists(self):
        """Verifica que la función de candidatos populares existe."""
        sig = inspect.signature(get_popular_product_ids)
        params = list(sig.parameters.keys())
        self.assertIn("session", params)
        self.assertIn("limit", params)

    def test_cold_start_pool_function_exists(self):
        """Verifica que _cold_start_pool existe como helper interno."""
        sig = inspect.signature(_cold_start_pool)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["session", "pool_size", "category"])


# ---------------------------------------------------------------------------
# Tests de contrato
# ---------------------------------------------------------------------------

class TestContractIntegrity(unittest.TestCase):

    def test_rank_signature_unchanged(self):
        sig = inspect.signature(rank)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["candidates", "context"])

    def test_candidates_signature_preserved(self):
        sig = inspect.signature(get_candidates)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["request", "session"],
                         "get_candidates firma debe mantenerse")

    def test_output_keys_preserved(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=5,
        )
        products = [
            MockProducto("P-T", "SKU-T", "Test", "pkg",
                         margin_pct=0.3, strategic_priority=0.5),
        ]
        result = rank(candidates=products, context=ctx)
        self.assertGreater(len(result), 0)
        required = {"product_id", "sku", "name", "score",
                     "reason_codes", "explanation"}
        self.assertTrue(required.issubset(set(result[0].keys())))


# ---------------------------------------------------------------------------
# Tests de integración (requieren servidor en :8010)
# ---------------------------------------------------------------------------

class TestEndpointIntegration(unittest.TestCase):

    def test_endpoint_200_valid_customer(self):
        status, body = http("POST", "/recommendations", {
            "customer_id": "CUST-001",
            "page_type": "homepage",
            "slot": "hero",
            "limit": 5,
        })
        self.assertEqual(status, 200)
        self.assertIn("items", body)
        self.assertIn("recommendation_id", body)

    def test_endpoint_404_invalid_customer(self):
        status, _ = http("POST", "/recommendations", {
            "customer_id": "CUST-NOEXIST",
            "page_type": "homepage",
            "slot": "hero",
        })
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
