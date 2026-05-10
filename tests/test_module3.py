"""
Pruebas de verificacion - Modulo 3: Event Tracking
Requiere el servidor corriendo en http://127.0.0.1:8000
"""
import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:8000"


def req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


results = []
FAKE_REC_ID = "a1b2c3d4-0000-0000-0000-000000000001"


# T1 - POST product_view con todos los campos opcionales
status, body = req("POST", "/events", {
    "event_type": "product_view",
    "customer_id": "CUST-001",
    "entity_type": "product",
    "entity_id": "BOX-001",
    "properties": {"source": "test_suite"},
})
ok = (status == 201
      and body.get("event_type") == "product_view"
      and "event_id" in body
      and body.get("schema_version") == 1
      and body.get("timestamp") is not None
      and body.get("customer_id") == "CUST-001")
results.append(("T01 POST product_view completo", ok, status,
                body.get("event_id", body)))

# T2 - POST search anonimo (sin customer_id)
status, body = req("POST", "/events", {
    "event_type": "search",
    "entity_type": "search",
    "entity_id": "caja pizza",
    "properties": {"query": "caja pizza", "results_count": 5},
})
ok = status == 201 and body.get("customer_id") is None
results.append(("T02 POST search anonimo", ok, status,
                body.get("event_id", body)))

# T3 - POST add_to_cart
status, body = req("POST", "/events", {
    "event_type": "add_to_cart",
    "customer_id": "CUST-002",
    "entity_type": "product",
    "entity_id": "CUP-001",
})
ok = status == 201
results.append(("T03 POST add_to_cart", ok, status,
                body.get("event_id", body)))

# T4 - POST purchase
status, body = req("POST", "/events", {
    "event_type": "purchase",
    "customer_id": "CUST-003",
    "entity_type": "product",
    "entity_id": "WRAP-001",
    "properties": {"quantity": 2, "channel": "ecommerce"},
})
ok = status == 201
results.append(("T04 POST purchase", ok, status,
                body.get("event_id", body)))

# T5 - POST product_click
status, body = req("POST", "/events", {
    "event_type": "product_click",
    "customer_id": "CUST-001",
    "entity_type": "product",
    "entity_id": "LAB-001",
})
ok = status == 201
results.append(("T05 POST product_click", ok, status,
                body.get("event_id", body)))

# T6 - VALIDACION: recommendation_shown SIN entity_id => 422
status, body = req("POST", "/events", {
    "event_type": "recommendation_shown",
    "customer_id": "CUST-001",
})
ok = status == 422
detail = body.get("detail", "")
detail_str = detail if isinstance(detail, str) else str(detail)
results.append(("T06 recommendation_shown sin entity_id -> 422", ok, status,
                detail_str[:70]))

# T7 - VALIDACION: recommendation_clicked SIN entity_id => 422
status, body = req("POST", "/events", {
    "event_type": "recommendation_clicked",
})
ok = status == 422
results.append(("T07 recommendation_clicked sin entity_id -> 422", ok, status,
                "validacion OK"))

# T8 - recommendation_shown CON entity_id => 201
status, body = req("POST", "/events", {
    "event_type": "recommendation_shown",
    "customer_id": "CUST-001",
    "entity_type": "recommendation",
    "entity_id": FAKE_REC_ID,
})
ok = status == 201 and body.get("entity_id") == FAKE_REC_ID
results.append(("T08 recommendation_shown con entity_id -> 201", ok, status,
                body.get("event_id", body)))

# T9 - recommendation_clicked CON entity_id => 201
status, body = req("POST", "/events", {
    "event_type": "recommendation_clicked",
    "customer_id": "CUST-001",
    "entity_type": "recommendation",
    "entity_id": FAKE_REC_ID,
})
ok = status == 201
results.append(("T09 recommendation_clicked con entity_id -> 201", ok, status,
                body.get("event_id", body)))

# T10 - GET /events lista
status, body = req("GET", "/events")
ok = status == 200 and isinstance(body, list) and len(body) >= 7
results.append(("T10 GET /events devuelve lista >= 7", ok, status,
                str(len(body)) + " eventos"))

# T11 - GET filtro customer_id
status, body = req("GET", "/events?customer_id=CUST-001")
ok = (status == 200
      and len(body) > 0
      and all(e["customer_id"] == "CUST-001" for e in body))
results.append(("T11 GET ?customer_id=CUST-001 filtra correcto", ok, status,
                str(len(body)) + " eventos del cliente"))

# T12 - GET filtro event_type
status, body = req("GET", "/events?event_type=product_view")
ok = (status == 200
      and len(body) > 0
      and all(e["event_type"] == "product_view" for e in body))
results.append(("T12 GET ?event_type=product_view filtra correcto", ok, status,
                str(len(body)) + " eventos"))

# T13 - GET limit=2
status, body = req("GET", "/events?limit=2")
ok = status == 200 and len(body) <= 2
results.append(("T13 GET ?limit=2 respeta el limite", ok, status,
                str(len(body)) + " eventos (max 2)"))

# T14 - GET limit=300 rechazado por validacion
status, body = req("GET", "/events?limit=300")
ok = status == 422
results.append(("T14 GET ?limit=300 rechazado -> 422", ok, status,
                "validacion OK"))

# T15 - Orden descendente por timestamp
status, body = req("GET", "/events")
if status == 200 and len(body) >= 2:
    timestamps = [e["timestamp"] for e in body]
    ok = timestamps == sorted(timestamps, reverse=True)
    results.append(("T15 Orden timestamp DESC correcto", ok, status,
                    "orden correcto"))
else:
    results.append(("T15 Orden timestamp DESC correcto", None, status,
                    "SKIP"))

# T16 - schema_version siempre es 1
status, body = req("GET", "/events?limit=10")
ok = status == 200 and all(e.get("schema_version") == 1 for e in body)
results.append(("T16 schema_version=1 en todos los eventos", ok, status,
                "todos v1"))

# T17 - evento tipo invalido rechazado
status, body = req("POST", "/events", {"event_type": "invalid_type"})
ok = status == 422
results.append(("T17 event_type invalido -> 422", ok, status,
                "validacion OK"))

# --------------------------------------------------------------------------
# RESUMEN
# --------------------------------------------------------------------------
SEP = "=" * 72
print()
print(SEP)
header = "TEST" + " " * 41 + "RESULT  HTTP"
print(header)
print(SEP)

passed = 0
skipped = 0
failed = 0

for name, ok, status, detail in results:
    if ok is None:
        icon = "?"
        tag = "SKIP"
        skipped += 1
    elif ok:
        icon = "V"
        tag = "PASS"
        passed += 1
    else:
        icon = "X"
        tag = "FAIL"
        failed += 1

    line = "[{}] {:<47} {:<6} {}".format(icon, name, tag, status)
    print(line)
    if not ok and ok is not None:
        print("     -> {}".format(str(detail)[:65]))

print(SEP)
total = len(results) - skipped
print("Resultado final: {}/{} pruebas pasaron  |  {} fallaron  |  {} omitidas".format(
    passed, total, failed, skipped))
print()
