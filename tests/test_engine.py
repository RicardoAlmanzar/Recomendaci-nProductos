from app.engine.scorer import build_recommendations
from app.models import Compra, Cliente, Producto, Regla

def test_build_recommendations_sorts_by_score():
    customer = Cliente(customer_id="CUST-001", business_type="pharmacy", city="Santiago", average_order_value=1200)
    catalog = [
        Producto(product_id="BOX-001", sku="BOX-1", name="Caja 1", category="boxes", margin_pct=0.35, strategic_priority=0.9),
        Producto(product_id="LAB-001", sku="LAB-1", name="Etiqueta 1", category="labels", margin_pct=0.1, strategic_priority=0.2),
    ]
    rules = [Regla(source_category="packaging", target_category="boxes", weight=0.9, reason_code="CROSS_SELL_RULE")]
    purchases = [Compra(customer_id="CUST-001", product_id="OLD-001", quantity=1, channel="sales_rep", city="Santiago")]

    recommendations = build_recommendations(customer, catalog, rules, purchases, limit=5)

    assert len(recommendations) == 2
    assert recommendations[0]["product_id"] == "BOX-001"
    assert "HIGH_MARGIN" in recommendations[0]["reason_codes"]
    assert recommendations[1]["product_id"] == "LAB-001"
