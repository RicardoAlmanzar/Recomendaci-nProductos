"""
Diagnostico COMPLETO cold-start — Modulo 11.
1. Inserta un cliente sin compras en la DB
2. Traza get_candidates(), rank(), y build_recommendations() paso a paso
3. Prueba el endpoint real POST /recommendations
4. Limpia el cliente de prueba
"""
import sys
import os

# Aseguramos que el proyecto este en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.db.session import engine
from app.models import Cliente, Producto, Regla, Compra
from app.engine.candidates import get_candidates
from app.engine.ranker import rank
from app.engine.scorer import build_recommendations
from app.models.recommendation import RecommendationRequest

SEP = "=" * 72
COLD_CUSTOMER_ID = "CUST-COLDSTART-TEST"


def main():
    print()
    print(SEP)
    print("DIAGNOSTICO COLD-START — TRAZA COMPLETA")
    print(SEP)

    with Session(engine) as session:
        # ── Paso 0: Crear cliente sin compras ──────────────────────────
        existing = session.get(Cliente, COLD_CUSTOMER_ID)
        if not existing:
            cold_customer = Cliente(
                customer_id=COLD_CUSTOMER_ID,
                business_type="test",
                city="TestCity",
                average_order_value=500,
            )
            session.add(cold_customer)
            session.commit()
            print("\n[+] Cliente '{}' creado (sin compras)".format(COLD_CUSTOMER_ID))
        else:
            print("\n[i] Cliente '{}' ya existe".format(COLD_CUSTOMER_ID))

        # Verificar que NO tiene compras
        purchases = session.exec(
            select(Compra).where(Compra.customer_id == COLD_CUSTOMER_ID)
        ).all()
        print("[i] Compras del cliente: {} (esperado: 0)".format(len(purchases)))
        assert len(purchases) == 0, "El cliente de prueba tiene compras!"

        # ── Paso 1: get_candidates() ──────────────────────────────────
        print("\n" + SEP)
        print("PASO 1: get_candidates()")
        print(SEP)

        request = RecommendationRequest(
            customer_id=COLD_CUSTOMER_ID,
            page_type="homepage",
            slot="hero",
            limit=5,
        )

        candidates = get_candidates(request, session)
        print("  Candidatos retornados: {}".format(len(candidates)))
        for p in candidates:
            print("    {} | {} | cat={} | margin={} | priority={} | active={}".format(
                p.product_id, p.name, p.category,
                p.margin_pct, p.strategic_priority, p.active))

        # ── Paso 2: Lo que rank()/build_recommendations() hace ────────
        print("\n" + SEP)
        print("PASO 2: build_recommendations() traza interna")
        print(SEP)

        customer = session.get(Cliente, COLD_CUSTOMER_ID)
        affinity_rules = session.exec(select(Regla)).all()

        print("  purchased_product_ids: {} (vacio)".format(set()))
        print("  purchased_categories: {} (vacio)".format(set()))
        print("  Reglas de afinidad disponibles: {}".format(len(affinity_rules)))
        print("  -> Todas las reglas seran SKIPPED (source_category not in empty set)")
        print("  -> rule_score de cada producto = 0")
        print()
        print("  add_margin_boost() para cada candidato:")

        from app.engine.rules import ScoreSlot, add_margin_boost
        for p in candidates:
            slot = ScoreSlot(product=p)
            add_margin_boost(slot)
            print("    {} -> margin_boost={:.4f} + strategic_boost={:.4f} = score={:.4f} {}".format(
                p.product_id,
                slot.margin_boost,
                slot.strategic_boost,
                slot.score,
                "PASA (>0)" if slot.score > 0 else "FILTRADO (=0)"))

        # ── Paso 3: rank() real ───────────────────────────────────────
        print("\n" + SEP)
        print("PASO 3: rank() — resultado real")
        print(SEP)

        ranked = rank(
            candidates=candidates,
            customer=customer,
            affinity_rules=affinity_rules,
            purchases=[],   # sin compras
            limit=5,
        )

        print("  Items retornados por rank(): {}".format(len(ranked)))
        for i, r in enumerate(ranked):
            print("    #{} {} (score={}, reasons={})".format(
                i + 1, r["name"], r["score"], r["reason_codes"]))

        # ── Paso 4: Prueba real del endpoint ──────────────────────────
        print("\n" + SEP)
        print("PASO 4: Prueba real POST /recommendations")
        print(SEP)

        import urllib.request
        import json

        data = json.dumps({
            "customer_id": COLD_CUSTOMER_ID,
            "page_type": "homepage",
            "slot": "hero",
            "limit": 5,
        }).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:8000/recommendations",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                body = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            status = e.code
            body = json.loads(e.read())

        print("  Status: {}".format(status))
        items = body.get("items", [])
        print("  Items en respuesta: {}".format(len(items)))
        print("  recommendation_id: {}".format(body.get("recommendation_id", "N/A")))
        print("  cache_hit: {}".format(body.get("cache_hit")))
        print("  algo_version: {}".format(body.get("algo_version")))

        if items:
            print()
            for item in items:
                print("    #{} {} | cat={} | score={} | reasons={}".format(
                    item["rank_position"], item["name"],
                    item["category"], item["score"], item["reason_codes"]))

        # ── VEREDICTO ─────────────────────────────────────────────────
        print("\n" + SEP)
        if status == 200 and len(items) > 0:
            print("VEREDICTO: COLD-START FUNCIONA CORRECTAMENTE")
            print("  El cliente sin compras recibe {} recomendaciones.".format(len(items)))
            print("  Los scores vienen de margin_boost + strategic_boost (sin reglas).")
        elif status == 200 and len(items) == 0:
            print("VEREDICTO: COLD-START ROTO")
            print("  El endpoint retorna 200 pero con items vacio.")
            print("  build_recommendations() filtra todo por score > 0.")
            print("  HAY QUE CORREGIR el pipeline.")
        else:
            print("VEREDICTO: ERROR INESPERADO (status={})".format(status))
            print("  Body: {}".format(json.dumps(body, indent=2)[:300]))
        print(SEP)

        # ── Limpieza ──────────────────────────────────────────────────
        cold = session.get(Cliente, COLD_CUSTOMER_ID)
        if cold:
            session.delete(cold)
            session.commit()
            print("\n[i] Cliente de prueba eliminado.")


if __name__ == "__main__":
    main()
