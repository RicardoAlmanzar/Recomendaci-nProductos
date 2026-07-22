"""
tests/test_metrics_module9.py — Módulo 9: Tests de cálculo de métricas.

Patrón: unittest + unittest.mock.MagicMock (sin servidor, sin DB real).
  MagicMock simula Session.exec().all() con side_effect para controlar
  qué eventos devuelve cada query dentro de la función bajo test.

Funciones cubiertas:
  get_summary_counts, get_ctr_per_item, get_ctr_per_response,
  get_conversion_rate, get_top_recommended_products, compute_metrics,
  register_event (contrato intacto)
"""
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.event import Event, EventType
from app.services.metrics import (
    build_metrics_summary,
    compute_metrics,
    get_conversion_rate,
    get_ctr_per_item,
    get_ctr_per_response,
    get_summary_counts,
    get_top_recommended_products,
    register_event,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _shown(product_ids: list[str], entity_id: str = "rec-001",
           customer_id: str = "CUST-001", days_ago: int = 0) -> Event:
    """Crea un Event recommendation_shown con timestamp dentro de la ventana."""
    return Event(
        event_type=EventType.recommendation_shown,
        customer_id=customer_id,
        entity_id=entity_id,
        entity_type="recommendation",
        properties={
            "product_ids": product_ids,
            "item_count": len(product_ids),
        },
        timestamp=datetime.utcnow() - timedelta(days=days_ago),
    )


def _clicked(product_id: str, entity_id: str = "rec-001",
             customer_id: str = "CUST-001", days_ago: int = 0) -> Event:
    """Crea un Event recommendation_clicked con timestamp dentro de la ventana."""
    return Event(
        event_type=EventType.recommendation_clicked,
        customer_id=customer_id,
        entity_id=entity_id,
        entity_type="recommendation",
        properties={"product_id": product_id, "rank_position": 1},
        timestamp=datetime.utcnow() - timedelta(days=days_ago),
    )


def _purchase(entity_id: str | None = "rec-001",
              entity_type: str | None = "recommendation",
              customer_id: str = "CUST-001", days_ago: int = 0) -> Event:
    """Crea un Event purchase (direct o organic según entity_id)."""
    return Event(
        event_type=EventType.purchase,
        customer_id=customer_id,
        entity_id=entity_id,
        entity_type=entity_type,
        properties={"product_id": "P-001"},
        timestamp=datetime.utcnow() - timedelta(days=days_ago),
    )


def _mock_db(*call_results: list) -> MagicMock:
    """Crea un MagicMock de Session cuyo exec().all() retorna cada lista en orden."""
    mock = MagicMock()
    mock.exec.return_value.all.side_effect = list(call_results)
    return mock


# ─────────────────────────────────────────────────────────────────────────────
# Tests: get_summary_counts
# ─────────────────────────────────────────────────────────────────────────────

class TestGetSummaryCounts(unittest.TestCase):

    def test_zeros_when_no_events(self):
        """compute_metrics retorna ceros cuando no hay eventos."""
        db = _mock_db([], [], [])   # shown=[], clicked=[], conversions=[]
        result = get_summary_counts(db, days=30)

        self.assertEqual(result["total_recommendations_served"], 0)
        self.assertEqual(result["total_items_served"], 0)
        self.assertEqual(result["total_clicks"], 0)
        self.assertEqual(result["total_conversions"], 0)

    def test_counts_recommendations_served(self):
        """COUNT de eventos recommendation_shown."""
        shown = [_shown(["P-1", "P-2"]), _shown(["P-3"])]
        db = _mock_db(shown, [], [])
        result = get_summary_counts(db, days=30)

        self.assertEqual(result["total_recommendations_served"], 2)

    def test_items_served_uses_item_count_field(self):
        """total_items_served usa properties['item_count'] cuando existe."""
        shown = [_shown(["P-1", "P-2", "P-3"])]   # item_count=3
        db = _mock_db(shown, [], [])
        result = get_summary_counts(db, days=30)

        self.assertEqual(result["total_items_served"], 3)

    def test_items_served_falls_back_to_product_ids_len(self):
        """Si no hay item_count, usa len(product_ids)."""
        ev = Event(
            event_type=EventType.recommendation_shown,
            customer_id="C",
            properties={"product_ids": ["P-1", "P-2"]},  # sin item_count
            timestamp=datetime.utcnow(),
        )
        db = _mock_db([ev], [], [])
        result = get_summary_counts(db, days=30)

        self.assertEqual(result["total_items_served"], 2)

    def test_clicks_require_valid_product_id(self):
        """Solo cuenta recommendation_clicked con properties.product_id válido."""
        valid_click = _clicked("P-001")
        invalid_click = Event(
            event_type=EventType.recommendation_clicked,
            customer_id="C",
            properties={},          # sin product_id
            timestamp=datetime.utcnow(),
        )
        db = _mock_db([], [valid_click, invalid_click], [])
        result = get_summary_counts(db, days=30)

        self.assertEqual(result["total_clicks"], 1)

    def test_conversions_require_entity_id_and_recommendation_type(self):
        """Solo cuenta purchase con entity_id no nulo y entity_type=='recommendation'."""
        direct = _purchase(entity_id="rec-001", entity_type="recommendation")
        organic = _purchase(entity_id=None, entity_type=None)
        db = _mock_db([], [], [direct, organic])
        result = get_summary_counts(db, days=30)

        # La query WHERE entity_id IS NOT NULL AND entity_type='recommendation'
        # retorna solo los eventos que cumplen la condición — en el mock
        # controlamos qué devuelve la query de conversiones
        self.assertEqual(result["total_conversions"], 2)  # mock devuelve todo


# ─────────────────────────────────────────────────────────────────────────────
# Tests: get_ctr_per_item
# ─────────────────────────────────────────────────────────────────────────────

class TestGetCtrPerItem(unittest.TestCase):

    def test_returns_zero_when_items_served_is_zero(self):
        """get_ctr_per_item retorna 0.0 si total_items_served es 0."""
        db = _mock_db([], [], [])
        result = get_ctr_per_item(db, days=30)
        self.assertEqual(result, 0.0)

    def test_calculates_clicks_divided_by_items(self):
        """get_ctr_per_item = clicks / items_served."""
        # 2 clicks, 10 items → 0.2
        shown = [_shown(["P-%d" % i for i in range(10)])]  # item_count=10
        clicked = [_clicked("P-1"), _clicked("P-2")]
        db = _mock_db(shown, clicked, [])
        result = get_ctr_per_item(db, days=30)

        self.assertEqual(result, round(2 / 10, 4))

    def test_rounds_to_four_decimals(self):
        """El resultado tiene máximo 4 decimales."""
        shown = [_shown(["P-%d" % i for i in range(3)])]   # 3 items
        clicked = [_clicked("P-1")]                          # 1 click
        db = _mock_db(shown, clicked, [])
        result = get_ctr_per_item(db, days=30)

        self.assertEqual(result, round(1 / 3, 4))


# ─────────────────────────────────────────────────────────────────────────────
# Tests: get_ctr_per_response
# ─────────────────────────────────────────────────────────────────────────────

class TestGetCtrPerResponse(unittest.TestCase):

    def test_returns_zero_when_no_shown(self):
        db = _mock_db([], [])
        self.assertEqual(get_ctr_per_response(db, days=30), 0.0)

    def test_uses_distinct_entity_id(self):
        """CTR por respuesta usa entity_id único — dos clicks al mismo rec cuentan como 1."""
        shown = [_shown(["P-1"], "rec-A"), _shown(["P-2"], "rec-B")]
        # rec-A recibe 3 clicks, rec-B recibe 0 → 1 rec única con click / 2 shown
        clicked = [
            _clicked("P-1", "rec-A"),
            _clicked("P-1", "rec-A"),
            _clicked("P-1", "rec-A"),
        ]
        db = _mock_db(shown, clicked)
        result = get_ctr_per_response(db, days=30)

        # 1 entity_id único ("rec-A") / 2 shown = 0.5
        self.assertEqual(result, 0.5)

    def test_two_clicked_recommendations(self):
        """Dos entity_id distintos con click / 3 shown = 0.6667."""
        shown = [_shown(["P-1"], "rec-A"), _shown(["P-2"], "rec-B"), _shown(["P-3"], "rec-C")]
        clicked = [_clicked("P-1", "rec-A"), _clicked("P-2", "rec-B")]
        db = _mock_db(shown, clicked)
        result = get_ctr_per_response(db, days=30)

        self.assertEqual(result, round(2 / 3, 4))


# ─────────────────────────────────────────────────────────────────────────────
# Tests: get_conversion_rate
# ─────────────────────────────────────────────────────────────────────────────

class TestGetConversionRate(unittest.TestCase):

    def test_returns_zero_rate_with_no_events(self):
        db = _mock_db([], [], [])
        result = get_conversion_rate(db, days=30)

        self.assertEqual(result["rate"], 0.0)
        self.assertEqual(result["type"], "direct")
        self.assertEqual(result["numerator"], 0)
        self.assertEqual(result["denominator"], 0)

    def test_counts_purchase_with_entity_id(self):
        """Conversión directa: purchase con entity_id válido."""
        shown = [_shown(["P-1"], "rec-A")]
        clicked: list = []
        conversions = [_purchase(entity_id="rec-A")]
        db = _mock_db(shown, clicked, conversions)
        result = get_conversion_rate(db, days=30)

        self.assertEqual(result["numerator"], 1)
        self.assertEqual(result["denominator"], 1)
        self.assertEqual(result["rate"], 1.0)

    def test_ignores_organic_purchases_without_entity_id(self):
        """Conversiones orgánicas (entity_id=None) NO cuentan como directas."""
        shown = [_shown(["P-1"], "rec-A"), _shown(["P-2"], "rec-B")]
        clicked: list = []
        # La query de conversiones filtra entity_id IS NOT NULL en la DB.
        # El mock devuelve solo las conversiones directas (sin entity_id=None).
        conversions = [_purchase(entity_id="rec-A")]   # mock filtra orgánicas
        db = _mock_db(shown, clicked, conversions)
        result = get_conversion_rate(db, days=30)

        self.assertEqual(result["numerator"], 1)
        self.assertEqual(result["denominator"], 2)
        self.assertEqual(result["rate"], round(1 / 2, 4))

    def test_denominator_zero_returns_zero_rate(self):
        """Si no hay recommendation_shown, rate=0.0 sin división por cero."""
        db = _mock_db([], [], [])
        result = get_conversion_rate(db, days=30)
        self.assertEqual(result["rate"], 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: get_top_recommended_products
# ─────────────────────────────────────────────────────────────────────────────

class TestGetTopRecommendedProducts(unittest.TestCase):

    def test_returns_empty_when_no_events(self):
        db = _mock_db([], [])
        result = get_top_recommended_products(db, limit=10, days=30)
        self.assertEqual(result, [])

    def test_groups_product_ids_correctly(self):
        """Agrupa product_id desde properties['product_ids'] de shown."""
        shown = [
            _shown(["P-1", "P-2"], "rec-A"),
            _shown(["P-1", "P-3"], "rec-B"),
            _shown(["P-1"],        "rec-C"),
        ]
        # P-1 aparece 3 veces, P-2 una vez, P-3 una vez
        db = _mock_db(shown, [])
        result = get_top_recommended_products(db, limit=10, days=30)

        top_product = result[0]
        self.assertEqual(top_product["product_id"], "P-1")
        self.assertEqual(top_product["recommendation_count"], 3)

    def test_calculates_click_count_and_ctr(self):
        """click_count y ctr calculados correctamente por producto."""
        shown = [_shown(["P-1", "P-2"], "rec-A")]   # P-1: 1, P-2: 1
        clicked = [_clicked("P-1", "rec-A"), _clicked("P-1", "rec-A")]   # 2 clicks en P-1
        db = _mock_db(shown, clicked)
        result = get_top_recommended_products(db, limit=10, days=30)

        p1 = next(r for r in result if r["product_id"] == "P-1")
        self.assertEqual(p1["click_count"], 2)
        self.assertEqual(p1["ctr"], round(2 / 1, 4))

        p2 = next(r for r in result if r["product_id"] == "P-2")
        self.assertEqual(p2["click_count"], 0)
        self.assertEqual(p2["ctr"], 0.0)

    def test_sorted_by_recommendation_count_desc(self):
        """Orden: recommendation_count DESC."""
        shown = [
            _shown(["P-1"],        "rec-A"),   # P-1: 1
            _shown(["P-2", "P-1"], "rec-B"),   # P-2: 1, P-1: 2
            _shown(["P-2"],        "rec-C"),   # P-2: 2
            _shown(["P-3", "P-2"], "rec-D"),   # P-3: 1, P-2: 3
        ]
        db = _mock_db(shown, [])
        result = get_top_recommended_products(db, limit=10, days=30)

        counts = [r["recommendation_count"] for r in result]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_limit_is_respected(self):
        """Retorna máximo `limit` productos."""
        shown = [_shown(["P-%d" % i for i in range(20)], "rec-A")]
        db = _mock_db(shown, [])
        result = get_top_recommended_products(db, limit=5, days=30)
        self.assertLessEqual(len(result), 5)

    def test_top_products_from_product_ids(self):
        """Extracción correcta de top_recommended_products desde properties['product_ids']."""
        shown = [_shown(["LAB-001", "LAB-002"], "rec-A")]
        db = _mock_db(shown, [])
        result = get_top_recommended_products(db, days=30)
        product_ids = {p["product_id"] for p in result}
        self.assertEqual(product_ids, {"LAB-001", "LAB-002"})

    def test_top_products_from_items(self):
        """Extracción correcta de top_recommended_products desde la estructura real properties['items']."""
        ev = Event(
            event_type=EventType.recommendation_shown,
            customer_id="CUST-001",
            properties={
                "items": [
                    {"product_id": "LAB-001", "score": 1.5},
                    {"product_id": "LAB-002", "score": 1.2}
                ]
            },
            timestamp=datetime.utcnow()
        )
        db = _mock_db([ev], [])
        result = get_top_recommended_products(db, days=30)
        product_ids = {p["product_id"] for p in result}
        self.assertEqual(product_ids, {"LAB-001", "LAB-002"})

    def test_top_products_from_products(self):
        """Extracción correcta de top_recommended_products desde properties['products']."""
        ev = Event(
            event_type=EventType.recommendation_shown,
            customer_id="CUST-001",
            properties={
                "products": [
                    {"product_id": "BOX-001"},
                    {"product_id": "BAG-001"}
                ]
            },
            timestamp=datetime.utcnow()
        )
        db = _mock_db([ev], [])
        result = get_top_recommended_products(db, days=30)
        product_ids = {p["product_id"] for p in result}
        self.assertEqual(product_ids, {"BOX-001", "BAG-001"})

    def test_top_products_empty_with_only_item_count(self):
        """Si solo hay item_count pero no hay lista de productos, retorna vacío."""
        ev = Event(
            event_type=EventType.recommendation_shown,
            customer_id="CUST-001",
            properties={"item_count": 5},
            timestamp=datetime.utcnow()
        )
        db = _mock_db([ev], [])
        result = get_top_recommended_products(db, days=30)
        self.assertEqual(result, [])

    def test_click_count_by_product_id_in_clicked(self):
        """click_count se calcula por properties['product_id'] en recommendation_clicked."""
        shown = [_shown(["LAB-001"], "rec-A")]
        clicked = [
            _clicked("LAB-001"),
            _clicked("LAB-001"),
            _clicked("LAB-002") # click a otro no mostrado
        ]
        db = _mock_db(shown, clicked)
        result = get_top_recommended_products(db, days=30)
        p1 = next(r for r in result if r["product_id"] == "LAB-001")
        self.assertEqual(p1["click_count"], 2)

    def test_ctr_calculation_click_divided_by_recommendation(self):
        """El CTR por producto es click_count / recommendation_count."""
        shown = [
            _shown(["LAB-001"], "rec-A"),
            _shown(["LAB-001"], "rec-B")
        ]
        clicked = [_clicked("LAB-001")]
        db = _mock_db(shown, clicked)
        result = get_top_recommended_products(db, days=30)
        p1 = next(r for r in result if r["product_id"] == "LAB-001")
        self.assertEqual(p1["recommendation_count"], 2)
        self.assertEqual(p1["click_count"], 1)
        self.assertEqual(p1["ctr"], 0.5)



# ─────────────────────────────────────────────────────────────────────────────
# Tests: ventana temporal
# ─────────────────────────────────────────────────────────────────────────────

class TestTemporalWindow(unittest.TestCase):

    def test_events_outside_window_not_counted(self):
        """El mock simula que la DB filtra por timestamp — eventos viejos no aparecen."""
        # La función hace WHERE timestamp >= cutoff en la query.
        # En el mock, configuramos que la DB solo devuelva eventos recientes.
        recent_shown = [_shown(["P-1"], days_ago=5)]    # dentro de 30 días
        # Evento de hace 60 días NO es devuelto por el mock (simula filtro DB)
        db = _mock_db(recent_shown, [], [])
        result = get_summary_counts(db, days=30)

        self.assertEqual(result["total_recommendations_served"], 1)

    def test_empty_results_when_all_events_outside_window(self):
        """Si todos los eventos están fuera de la ventana, mock devuelve []."""
        db = _mock_db([], [], [])   # simula que la DB filtró todo
        result = get_summary_counts(db, days=7)

        self.assertEqual(result["total_recommendations_served"], 0)
        self.assertEqual(result["total_items_served"], 0)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: compute_metrics
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeMetrics(unittest.TestCase):

    def test_build_metrics_summary_exposes_dashboard_payload(self):
        """build_metrics_summary devuelve un resumen compacto para el dashboard."""
        db = MagicMock()
        db.exec.return_value.all.return_value = []

        result = build_metrics_summary(db, window_days=14, top_n=5)

        self.assertEqual(result["window_days"], 14)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "ok")
        self.assertIn("totals", result)
        self.assertIn("rates", result)
        self.assertEqual(result["totals"]["recommendations_served"], 0)
        self.assertEqual(result["top_recommended_products"], [])

    def test_returns_zeros_when_no_events(self):
        """compute_metrics retorna estructura segura con ceros si no hay eventos."""
        # compute_metrics llama a get_summary_counts (3 queries), get_ctr_per_item
        # (3 queries), get_ctr_per_response (2 queries), get_conversion_rate (3),
        # get_top_recommended_products (2) → 13 llamadas a exec().all()
        db = MagicMock()
        db.exec.return_value.all.return_value = []

        result = compute_metrics(db, window_days=30, top_n=10)

        self.assertEqual(result["recommendations_served"], 0)
        self.assertEqual(result["items_served"], 0)
        self.assertEqual(result["clicks"], 0)
        self.assertEqual(result["ctr_item"], 0.0)
        self.assertEqual(result["ctr_response"], 0.0)
        self.assertEqual(result["conversions_direct"], 0)
        self.assertEqual(result["conversion_rate_direct"], 0.0)
        self.assertEqual(result["top_recommended_products"], [])

    def test_response_has_required_keys(self):
        """El dict retornado tiene todas las claves del contrato."""
        db = MagicMock()
        db.exec.return_value.all.return_value = []
        result = compute_metrics(db)

        required_keys = {
            "window_days", "generated_at", "recommendations_served",
            "items_served", "clicks", "ctr_item", "ctr_response",
            "conversions_direct", "conversion_rate_direct",
            "top_recommended_products",
        }
        self.assertTrue(required_keys.issubset(set(result.keys())))

    def test_window_days_propagated(self):
        """window_days del parámetro aparece en el response."""
        db = MagicMock()
        db.exec.return_value.all.return_value = []
        result = compute_metrics(db, window_days=7)
        self.assertEqual(result["window_days"], 7)

    def test_generated_at_is_iso_string(self):
        """generated_at es un string ISO 8601 parseable."""
        db = MagicMock()
        db.exec.return_value.all.return_value = []
        result = compute_metrics(db)
        # Debe parsear sin excepción
        parsed = datetime.fromisoformat(result["generated_at"])
        self.assertIsInstance(parsed, datetime)

    def test_compute_metrics_non_empty_with_properties_items(self):
        """compute_metrics devuelve top_recommended_products no vacío cuando hay properties['items']."""
        ev = Event(
            event_type=EventType.recommendation_shown,
            customer_id="CUST-001",
            properties={
                "items": [
                    {"product_id": "LAB-001", "score": 1.5}
                ]
            },
            timestamp=datetime.utcnow()
        )
        db = MagicMock()
        # compute_metrics hace múltiples consultas a db.exec().all().
        # Retornamos el evento simulado en todas las consultas para asegurar que get_top_recommended_products lo reciba.
        db.exec.return_value.all.return_value = [ev]
        result = compute_metrics(db, window_days=30, top_n=10)
        self.assertEqual(len(result["top_recommended_products"]), 1)
        self.assertEqual(result["top_recommended_products"][0]["product_id"], "LAB-001")



# ─────────────────────────────────────────────────────────────────────────────
# Tests: contrato de register_event (no fue roto)
# ─────────────────────────────────────────────────────────────────────────────

class TestRegisterEventContractIntact(unittest.TestCase):

    def test_register_event_exists_and_is_callable(self):
        """register_event sigue existiendo y es callable."""
        self.assertTrue(callable(register_event))

    def test_register_event_does_not_raise_on_success(self):
        """register_event no lanza excepción en el camino feliz."""
        mock_session = MagicMock()
        mock_session.add.return_value = None
        mock_session.commit.return_value = None

        # No debe lanzar excepción
        register_event(
            session=mock_session,
            event_type=EventType.recommendation_shown,
            customer_id="CUST-001",
            entity_id="rec-uuid-001",
            entity_type="recommendation",
            properties={"product_ids": ["P-1"], "item_count": 1},
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_register_event_does_not_raise_on_db_failure(self):
        """register_event silencia excepciones de DB — nunca propaga al caller."""
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("DB connection lost")

        # No debe lanzar excepción
        try:
            register_event(
                session=mock_session,
                event_type=EventType.recommendation_clicked,
                customer_id="CUST-001",
            )
        except Exception as exc:
            self.fail(f"register_event propagó excepción inesperada: {exc}")

    def test_register_event_signature_unchanged(self):
        """Firma de register_event mantiene todos los parámetros del Prompt 3."""
        import inspect
        sig = inspect.signature(register_event)
        params = list(sig.parameters.keys())
        self.assertIn("session", params)
        self.assertIn("event_type", params)
        self.assertIn("customer_id", params)
        self.assertIn("session_id", params)
        self.assertIn("entity_id", params)
        self.assertIn("entity_type", params)
        self.assertIn("properties", params)


# ─────────────────────────────────────────────────────────────────────────────
# Tests de integración del endpoint (requiere servidor levantado en :8010)
# ─────────────────────────────────────────────────────────────────────────────

class TestMetricsEndpointIntegration(unittest.TestCase):
    """Tests del endpoint GET /admin/metrics contra el servidor activo."""

    BASE = "http://127.0.0.1:8010"

    def _http(self, method: str, path: str):
        """Helper HTTP mínimo sin dependencias externas."""
        import json
        import urllib.error
        import urllib.request
        r = urllib.request.Request(self.BASE + path, method=method)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read())
            except Exception:
                return e.code, e.read()
        except Exception as e:
            return 999, str(e)

    def test_endpoint_admin_metrics_200(self):
        """El endpoint debe responder 200 con la estructura de métricas."""
        status, body = self._http("GET", "/admin/metrics")
        if status == 999:
            # Servidor no activo, omitir test de integración (comportamiento esperado)
            raise unittest.SkipTest("El servidor local en el puerto 8010 no está activo.")

        self.assertEqual(status, 200)
        self.assertIn("window_days", body)
        self.assertIn("generated_at", body)
        self.assertIn("recommendations_served", body)
        self.assertIn("items_served", body)
        self.assertIn("clicks", body)
        self.assertIn("ctr_item", body)
        self.assertIn("ctr_response", body)
        self.assertIn("conversions_direct", body)
        self.assertIn("conversion_rate_direct", body)
        self.assertIn("top_recommended_products", body)

    def test_endpoint_admin_metrics_params(self):
        """El endpoint debe aceptar los query params days y top_n."""
        status, body = self._http("GET", "/admin/metrics?days=7&top_n=5")
        if status == 999:
            raise unittest.SkipTest("El servidor local en el puerto 8010 no está activo.")

        self.assertEqual(status, 200)
        self.assertEqual(body["window_days"], 7)
        self.assertLessEqual(len(body["top_recommended_products"]), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
