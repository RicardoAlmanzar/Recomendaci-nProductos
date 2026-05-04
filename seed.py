from sqlmodel import Session, select

from app.db.session import engine, init_db
from app.models import Compra, Cliente, Producto, Regla


def _ensure_customer(session: Session, customer: Cliente) -> None:
	if not session.get(Cliente, customer.customer_id):
		session.add(customer)


def _ensure_product(session: Session, product: Producto) -> None:
	if not session.get(Producto, product.product_id):
		session.add(product)


def _ensure_rule(session: Session, rule: Regla) -> None:
	existing_rule = session.exec(
		select(Regla).where(
			Regla.source_category == rule.source_category,
			Regla.target_category == rule.target_category,
			Regla.reason_code == rule.reason_code,
		)
	).first()
	if not existing_rule:
		session.add(rule)


def _ensure_purchase(session: Session, purchase: Compra) -> None:
	existing_purchase = session.exec(
		select(Compra).where(
			Compra.customer_id == purchase.customer_id,
			Compra.product_id == purchase.product_id,
			Compra.quantity == purchase.quantity,
		)
	).first()
	if not existing_purchase:
		session.add(purchase)


def seed_data() -> None:
	init_db()

	with Session(engine) as session:
		customers = [
			Cliente(customer_id="CUST-001", business_type="pharmacy", city="Santiago", average_order_value=1200),
			Cliente(customer_id="CUST-002", business_type="bakery", city="Santo Domingo", average_order_value=900),
			Cliente(customer_id="CUST-003", business_type="ecommerce", city="Santo Domingo Este", average_order_value=1500),
			Cliente(customer_id="CUST-004", business_type="restaurant", city="La Vega", average_order_value=1800),
			Cliente(customer_id="CUST-005", business_type="office_supply", city="San Pedro de Macoris", average_order_value=1100),
		]
		products = [
			Producto(product_id="BOX-001", sku="BOX-PIZZA-12", name="Caja 12 pulgadas", category="packaging", margin_pct=0.35, strategic_priority=0.9),
			Producto(product_id="BOX-002", sku="BOX-GENERAL-01", name="Caja Multiuso", category="packaging", margin_pct=0.28, strategic_priority=0.7),
			Producto(product_id="BAG-001", sku="BAG-KRAFT-01", name="Bolsa Kraft", category="packaging", margin_pct=0.22, strategic_priority=0.65),
			Producto(product_id="TAPE-001", sku="TAPE-SELL-01", name="Cinta Selladora", category="packaging", margin_pct=0.25, strategic_priority=0.6),
			Producto(product_id="LAB-001", sku="LAB-STICK-01", name="Etiqueta Adhesiva", category="labels", margin_pct=0.31, strategic_priority=0.85),
			Producto(product_id="LAB-002", sku="LAB-THERM-01", name="Etiqueta Termica", category="labels", margin_pct=0.29, strategic_priority=0.8),
			Producto(product_id="CUP-001", sku="CUP-BIO-01", name="Vaso Biodegradable", category="food_service", margin_pct=0.33, strategic_priority=0.75),
			Producto(product_id="NAP-001", sku="NAP-PREM-01", name="Servilleta Premium", category="food_service", margin_pct=0.26, strategic_priority=0.55),
			Producto(product_id="THERM-001", sku="THERM-ROLL-01", name="Papel Termico", category="paper", margin_pct=0.34, strategic_priority=0.88),
			Producto(product_id="INK-001", sku="INK-FAST-01", name="Tinta para Impresora", category="paper", margin_pct=0.38, strategic_priority=0.82),
			Producto(product_id="RECEIPT-001", sku="RECEIPT-80MM", name="Papel Recibo", category="paper", margin_pct=0.24, strategic_priority=0.72),
			Producto(product_id="CLEAN-001", sku="CLEAN-DEGREASER", name="Desengrasante Industrial", category="cleaning", margin_pct=0.32, strategic_priority=0.6),
			Producto(product_id="CLEAN-002", sku="CLEAN-MICRO", name="Paño Microfibra", category="cleaning", margin_pct=0.27, strategic_priority=0.58),
			Producto(product_id="FILL-001", sku="FILL-PAPER", name="Relleno Protector", category="protective", margin_pct=0.21, strategic_priority=0.63),
			Producto(product_id="WRAP-001", sku="WRAP-STRETCH", name="Film Stretch", category="protective", margin_pct=0.3, strategic_priority=0.77),
		]
		rules = [
			Regla(source_category="packaging", target_category="labels", weight=0.9, reason_code="CROSS_SELL_RULE"),
			Regla(source_category="packaging", target_category="protective", weight=0.8, reason_code="CROSS_SELL_RULE"),
			Regla(source_category="food_service", target_category="packaging", weight=0.85, reason_code="CROSS_SELL_RULE"),
			Regla(source_category="food_service", target_category="labels", weight=0.7, reason_code="CROSS_SELL_RULE"),
			Regla(source_category="paper", target_category="labels", weight=0.82, reason_code="CROSS_SELL_RULE"),
			Regla(source_category="protective", target_category="packaging", weight=0.78, reason_code="CROSS_SELL_RULE"),
			Regla(source_category="cleaning", target_category="protective", weight=0.65, reason_code="CROSS_SELL_RULE"),
		]
		purchases = [
			Compra(customer_id="CUST-001", product_id="BOX-001", quantity=10, channel="sales_rep", city="Santiago"),
			Compra(customer_id="CUST-001", product_id="THERM-001", quantity=4, channel="sales_rep", city="Santiago"),
			Compra(customer_id="CUST-002", product_id="CUP-001", quantity=8, channel="whatsapp", city="Santo Domingo"),
			Compra(customer_id="CUST-002", product_id="NAP-001", quantity=12, channel="whatsapp", city="Santo Domingo"),
			Compra(customer_id="CUST-003", product_id="WRAP-001", quantity=6, channel="ecommerce", city="Santo Domingo Este"),
			Compra(customer_id="CUST-003", product_id="BAG-001", quantity=5, channel="ecommerce", city="Santo Domingo Este"),
			Compra(customer_id="CUST-004", product_id="CLEAN-001", quantity=3, channel="field_sales", city="La Vega"),
			Compra(customer_id="CUST-004", product_id="FILL-001", quantity=7, channel="field_sales", city="La Vega"),
			Compra(customer_id="CUST-005", product_id="RECEIPT-001", quantity=15, channel="sales_rep", city="San Pedro de Macoris"),
			Compra(customer_id="CUST-005", product_id="INK-001", quantity=2, channel="sales_rep", city="San Pedro de Macoris"),
		]

		for customer in customers:
			_ensure_customer(session, customer)

		for product in products:
			_ensure_product(session, product)

		session.commit()

		for rule in rules:
			_ensure_rule(session, rule)

		for purchase in purchases:
			_ensure_purchase(session, purchase)

		session.commit()
		print("Datos semilla cargados correctamente.")


if __name__ == "__main__":
	seed_data()
