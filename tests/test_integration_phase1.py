import unittest
import urllib.request
import urllib.error
import json
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlmodel import Session
from app.models import Cliente

BASE = "http://127.0.0.1:8010"

def req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

class TestIntegrationPhase1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Estado compartido entre tests (para pipeline completo)
        cls.state = {}

    def test_b1_recomendaciones_basicas_y_cache(self):
        # Primera peticion
        status, body = req("POST", "/recommendations", {
            "customer_id": "CUST-001", "page_type": "homepage",
            "slot": "hero", "limit": 5,
        })
        self.assertEqual(status, 200)
        
        rec_id = body.get("recommendation_id")
        self.assertIsNotNone(rec_id)
        uuid.UUID(rec_id) # No debe fallar
        
        items = body.get("items", [])
        self.assertEqual(len(items), 5)
        
        required_keys = {"product_id", "sku", "name", "category", "score", "rank_position", "reason_codes"}
        for item in items:
            self.assertTrue(required_keys.issubset(set(item.keys())))
            
        self.assertFalse(body.get("cache_hit"))
        self.assertIn("algo_version", body)
        
        # Guardamos en estado para siguientes tests
        self.__class__.state["rec_id"] = rec_id
        self.__class__.state["prod_1"] = items[0]["product_id"]

        # Segunda peticion (Cache hit)
        status2, body2 = req("POST", "/recommendations", {
            "customer_id": "CUST-001", "page_type": "homepage",
            "slot": "hero", "limit": 5,
        })
        self.assertEqual(status2, 200)
        self.assertTrue(body2.get("cache_hit"))
        self.assertEqual(body2.get("recommendation_id"), rec_id)

    def test_b2_filtro_por_categoria(self):
        status, body = req("POST", "/recommendations", {
            "customer_id": "CUST-002", "page_type": "product_detail",
            "slot": "related", "limit": 3,
            "context": {"category": "packaging"},
        })
        self.assertEqual(status, 200)
        items = body.get("items", [])
        self.assertGreater(len(items), 0)
        for item in items:
            self.assertEqual(item.get("category"), "packaging")

    def test_b3_cold_start_cliente_sin_historial(self):
        cold_id = "CUST-INT-COLD"
        with Session(engine) as session:
            if not session.get(Cliente, cold_id):
                session.add(Cliente(customer_id=cold_id, business_type="test", city="city", average_order_value=0))
                session.commit()
                
        status, body = req("POST", "/recommendations", {
            "customer_id": cold_id, "page_type": "cart", "slot": "sidebar",
        })
        self.assertEqual(status, 200)
        items = body.get("items", [])
        self.assertGreater(len(items), 0)
        for item in items:
            self.assertGreater(item.get("score", 0), 0)
            
        # Limpiar db
        from app.models.event import Event
        from sqlmodel import select
        with Session(engine) as session:
            # Primero borrar eventos que hacen referencia al cliente de prueba
            events = session.exec(select(Event).where(Event.customer_id == cold_id)).all()
            for e in events:
                session.delete(e)
            session.commit()

            c = session.get(Cliente, cold_id)
            if c:
                session.delete(c)
                session.commit()

    def test_b4_loop_completo_tracking(self):
        # Forzamos llamar a B1 primero si no ha corrido, o esperamos que unittest las corra en orden alfabético
        rec_id = self.__class__.state.get("rec_id")
        prod_id = self.__class__.state.get("prod_1")
        if not rec_id:
            self.test_b1_recomendaciones_basicas_y_cache()
            rec_id = self.__class__.state.get("rec_id")
            prod_id = self.__class__.state.get("prod_1")

        # Emitir shown
        status1, _ = req("POST", "/events", {
            "event_type": "recommendation_shown", "customer_id": "CUST-001",
            "entity_type": "recommendation", "entity_id": rec_id,
            "properties": {"slot": "hero", "item_count": 5},
        })
        self.assertEqual(status1, 201)
        
        # Emitir clicked
        status2, _ = req("POST", "/events", {
            "event_type": "recommendation_clicked", "customer_id": "CUST-001",
            "entity_type": "recommendation", "entity_id": rec_id,
            "properties": {"product_id": prod_id, "rank_position": 1},
        })
        self.assertEqual(status2, 201)
        
        # Verificar GET /events
        status3, body3 = req("GET", "/events?customer_id=CUST-001&event_type=recommendation_shown")
        self.assertEqual(status3, 200)
        events3 = body3 if isinstance(body3, list) else body3.get("events", [])
        self.assertTrue(any(e.get("entity_id") == rec_id for e in events3))
        
        status4, body4 = req("GET", "/events?customer_id=CUST-001&event_type=recommendation_clicked")
        self.assertEqual(status4, 200)
        events4 = body4 if isinstance(body4, list) else body4.get("events", [])
        self.assertTrue(any(e.get("entity_id") == rec_id and e.get("properties", {}).get("product_id") == prod_id for e in events4))

    def test_b5_debugging_por_recommendation_id(self):
        rec_id = self.__class__.state.get("rec_id")
        if not rec_id:
            self.test_b1_recomendaciones_basicas_y_cache()
            rec_id = self.__class__.state.get("rec_id")
            
        status, body = req("GET", f"/recommendations/{rec_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body.get("recommendation_id"), rec_id)
        
        status_falso, _ = req("GET", f"/recommendations/{uuid.uuid4()}")
        self.assertEqual(status_falso, 404)

    def test_b6_validaciones_y_edge_cases(self):
        status1, _ = req("POST", "/recommendations", {
            "customer_id": "CUST-NOEXIST", "page_type": "homepage", "slot": "hero"
        })
        self.assertEqual(status1, 404)
        
        status2, _ = req("POST", "/recommendations", {
            "customer_id": "CUST-001", "page_type": "homepage", "slot": "hero", "limit": 25
        })
        self.assertEqual(status2, 422)
        
        status3, _ = req("POST", "/events", {
            "event_type": "recommendation_shown", "customer_id": "CUST-001",
            "entity_type": "recommendation",
        })
        self.assertEqual(status3, 422)
        
        status4, _ = req("POST", "/recommendations", {
            "customer_id": "CUST-003", "slot": "hero"
        })
        self.assertEqual(status4, 422)

    def test_b7_consistencia_datos_entre_modulos(self):
        status, body = req("GET", "/events")
        self.assertEqual(status, 200)
        events = body if isinstance(body, list) else body.get("events", [])
        
        self.assertTrue(all(e.get("schema_version") == 1 for e in events))
        
        timestamps = [e.get("timestamp") for e in events]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))
        
        self.assertTrue(any(e.get("event_type") == "recommendation_shown" for e in events))
        self.assertTrue(any(e.get("event_type") == "recommendation_clicked" for e in events))

if __name__ == '__main__':
    unittest.main(verbosity=2)
