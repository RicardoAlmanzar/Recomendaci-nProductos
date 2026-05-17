"""
Tests del Módulo 5: Ranking.

Verifica que:
- rank() recibe (candidates, RankingContext) y devuelve lista ordenada.
- rank() respeta limit.
- rank() conserva reason_codes.
- El endpoint /recommendations sigue respondiendo 200 para cliente válido.
- Cliente inexistente devuelve 404.
- candidates.py no fue modificado (firma intacta).
"""
import inspect
import json
import os
import sys
import unittest
import urllib.error
import urllib.request

# Asegurar que el proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.ranker import RankingContext, rank
from app.engine.candidates import get_candidates


BASE = "http://127.0.0.1:8010"


def http(method: str, path: str, body=None):
    """Helper HTTP mínimo sin dependencias externas."""
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# ---------------------------------------------------------------------------
# Mocks mínimos para tests unitarios sin DB
# ---------------------------------------------------------------------------

class MockProducto:
    """Simula un Producto con los atributos que el scorer necesita."""
    def __init__(self, product_id, sku, name, category, active=True,
                 margin_pct=0.2, strategic_priority=0.5):
        self.product_id = product_id
        self.sku = sku
        self.name = name
        self.category = category
        self.active = active
        self.margin_pct = margin_pct
        self.strategic_priority = strategic_priority


class MockCliente:
    """Simula un Cliente."""
    def __init__(self, customer_id="CUST-TEST", business_type="retail",
                 city="Santo Domingo"):
        self.customer_id = customer_id
        self.business_type = business_type
        self.city = city


class MockCompra:
    """Simula una Compra."""
    def __init__(self, product_id):
        self.product_id = product_id


class MockRegla:
    """Simula una Regla de afinidad."""
    def __init__(self, source_category, target_category, weight=0.8,
                 reason_code="CROSS_SELL", active=True):
        self.source_category = source_category
        self.target_category = target_category
        self.weight = weight
        self.reason_code = reason_code
        self.active = active


# ---------------------------------------------------------------------------
# Tests unitarios
# ---------------------------------------------------------------------------

class TestRankingContext(unittest.TestCase):
    """Verifica que RankingContext se puede construir correctamente."""

    def test_context_creation_minimal(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=5,
        )
        self.assertEqual(ctx.limit, 5)
        self.assertIsNone(ctx.page_type)
        self.assertIsNone(ctx.slot)
        self.assertIsNone(ctx.session_id)
        self.assertIsNone(ctx.request_context)

    def test_context_creation_full(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[MockCompra("P-001")],
            affinity_rules=[MockRegla("cleaning", "packaging")],
            limit=10,
            page_type="homepage",
            slot="hero",
            session_id="sess-123",
            request_context={"category": "packaging"},
        )
        self.assertEqual(ctx.page_type, "homepage")
        self.assertEqual(ctx.slot, "hero")
        self.assertEqual(ctx.session_id, "sess-123")
        self.assertEqual(ctx.request_context, {"category": "packaging"})


class TestRankSignature(unittest.TestCase):
    """Verifica que la firma pública de rank() sea la del Módulo 5."""

    def test_rank_signature(self):
        sig = inspect.signature(rank)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["candidates", "context"],
                         f"La firma de rank() debe ser (candidates, context), "
                         f"pero es ({', '.join(params)})")

    def test_rank_returns_list(self):
        # Con candidatos vacíos, debe retornar lista vacía
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=[],
            affinity_rules=[],
            limit=5,
        )
        result = rank(candidates=[], context=ctx)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


class TestRankBehavior(unittest.TestCase):
    """Verifica el comportamiento de rank() con datos mockeados."""

    def setUp(self):
        # Productos de distintas categorías
        self.products = [
            MockProducto("P-001", "SKU-001", "Caja Corrugada", "packaging",
                         margin_pct=0.35, strategic_priority=0.9),
            MockProducto("P-002", "SKU-002", "Bolsa Kraft", "packaging",
                         margin_pct=0.15, strategic_priority=0.3),
            MockProducto("P-003", "SKU-003", "Desengrasante", "cleaning",
                         margin_pct=0.4, strategic_priority=0.7),
            MockProducto("P-004", "SKU-004", "Etiqueta Térmica", "labels",
                         margin_pct=0.25, strategic_priority=0.6),
            MockProducto("P-005", "SKU-005", "Stretch Film", "packaging",
                         margin_pct=0.30, strategic_priority=0.5),
        ]

        # Cliente que compró un producto de cleaning
        self.purchases = [MockCompra("P-003")]

        # Regla: quien compra cleaning → recomendar packaging
        self.rules = [
            MockRegla("cleaning", "packaging", weight=0.8,
                      reason_code="CROSS_SELL_CLEAN_PACK"),
        ]

    def test_rank_returns_ordered_by_score(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=self.purchases,
            affinity_rules=self.rules,
            limit=10,
        )
        result = rank(candidates=self.products, context=ctx)

        # Debe haber resultados (los packaging que matchean la regla)
        self.assertGreater(len(result), 0)

        # Verificar orden descendente por score
        scores = [r["score"] for r in result]
        self.assertEqual(scores, sorted(scores, reverse=True),
                         "Los resultados deben estar ordenados por score desc")

    def test_rank_respects_limit(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=self.purchases,
            affinity_rules=self.rules,
            limit=2,
        )
        result = rank(candidates=self.products, context=ctx)
        self.assertLessEqual(len(result), 2)

    def test_rank_conserves_reason_codes(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=self.purchases,
            affinity_rules=self.rules,
            limit=10,
        )
        result = rank(candidates=self.products, context=ctx)

        for item in result:
            self.assertIn("reason_codes", item)
            self.assertIsInstance(item["reason_codes"], list)

        # Al menos un item debe tener el reason_code de la regla
        all_codes = []
        for item in result:
            all_codes.extend(item["reason_codes"])
        self.assertIn("CROSS_SELL_CLEAN_PACK", all_codes)

    def test_rank_output_has_required_keys(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=self.purchases,
            affinity_rules=self.rules,
            limit=10,
        )
        result = rank(candidates=self.products, context=ctx)
        required_keys = {"product_id", "sku", "name", "score", "reason_codes",
                         "explanation"}

        for item in result:
            self.assertTrue(required_keys.issubset(set(item.keys())),
                            f"Faltan keys: {required_keys - set(item.keys())}")

    def test_rank_excludes_purchased_products(self):
        ctx = RankingContext(
            customer=MockCliente(),
            purchases=self.purchases,
            affinity_rules=self.rules,
            limit=10,
        )
        result = rank(candidates=self.products, context=ctx)
        result_ids = {r["product_id"] for r in result}

        # P-003 fue comprado, no debe aparecer
        self.assertNotIn("P-003", result_ids)


class TestCandidatesNotModified(unittest.TestCase):
    """Verifica que candidates.py mantiene su firma original."""

    def test_get_candidates_signature(self):
        sig = inspect.signature(get_candidates)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["request", "session"],
                         "candidates.py no debe haber sido modificado")


# ---------------------------------------------------------------------------
# Tests de integración (requieren servidor levantado en :8010)
# ---------------------------------------------------------------------------

class TestEndpointIntegration(unittest.TestCase):
    """Tests contra el endpoint real — requiere servidor en puerto 8010."""

    def test_endpoint_200_valid_customer(self):
        status, body = http("POST", "/recommendations", {
            "customer_id": "CUST-001",
            "page_type": "homepage",
            "slot": "hero",
            "limit": 5,
        })
        self.assertEqual(status, 200,
                         f"Endpoint debe responder 200 para CUST-001. Body: {body}")

        # Validar estructura de respuesta
        self.assertIn("recommendation_id", body)
        self.assertIn("items", body)
        self.assertIn("algo_version", body)

        items = body["items"]
        for item in items:
            self.assertIn("product_id", item)
            self.assertIn("sku", item)
            self.assertIn("name", item)
            self.assertIn("score", item)
            self.assertIn("rank_position", item)
            self.assertIn("reason_codes", item)

    def test_endpoint_404_invalid_customer(self):
        status, body = http("POST", "/recommendations", {
            "customer_id": "CUST-NOEXIST",
            "page_type": "homepage",
            "slot": "hero",
        })
        self.assertEqual(status, 404)

    def test_endpoint_items_ordered_by_rank_position(self):
        status, body = http("POST", "/recommendations", {
            "customer_id": "CUST-001",
            "page_type": "product_detail",
            "slot": "related",
            "limit": 5,
        })
        self.assertEqual(status, 200)
        items = body.get("items", [])
        positions = [i["rank_position"] for i in items]
        self.assertEqual(positions, list(range(1, len(positions) + 1)),
                         "rank_position debe ser secuencial empezando en 1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
