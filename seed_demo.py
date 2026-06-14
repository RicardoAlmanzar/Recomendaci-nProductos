"""
Script de demostración masiva de datos para la base de datos.
Inserta 50 productos, 20 clientes, 15+ reglas de afinidad, historial de compras realista,
y eventos de comportamiento para simular actividad del sistema.
"""

import random
import uuid
from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.db.session import engine, init_db
from app.models import Compra, Cliente, Producto, Regla
from app.models.event import Event, EventType


# ============================================================================
# HELPERS DE IDEMPOTENCIA (igual que en seed.py)
# ============================================================================

def _ensure_customer(session: Session, customer: Cliente) -> None:
    """Inserta cliente solo si no existe."""
    if not session.get(Cliente, customer.customer_id):
        session.add(customer)


def _ensure_product(session: Session, product: Producto) -> None:
    """Inserta producto solo si no existe."""
    if not session.get(Producto, product.product_id):
        session.add(product)


def _ensure_rule(session: Session, rule: Regla) -> None:
    """Inserta regla solo si no existe (por combinación de categorías y reason_code)."""
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
    """Inserta compra solo si no existe (por combinación de customer_id, product_id, quantity)."""
    existing_purchase = session.exec(
        select(Compra).where(
            Compra.customer_id == purchase.customer_id,
            Compra.product_id == purchase.product_id,
            Compra.quantity == purchase.quantity,
        )
    ).first()
    if not existing_purchase:
        session.add(purchase)


def _ensure_event(session: Session, event: Event) -> None:
    """Inserta evento solo si no existe (por combinación de customer_id, entity_id, event_type)."""
    # Para eventos, usamos una búsqueda menos restrictiva
    existing_event = session.exec(
        select(Event).where(
            Event.customer_id == event.customer_id,
            Event.event_type == event.event_type,
            Event.entity_id == event.entity_id,
        )
    ).first()
    if not existing_event:
        session.add(event)


# ============================================================================
# DATOS DE DEMOSTRACIÓN
# ============================================================================

CATEGORIAS = ["packaging", "labels", "food_service", "paper", "cleaning", "protective"]

CIUDADES = [
    "Santo Domingo",
    "Santiago",
    "La Vega",
    "San Pedro de Macorís",
    "Puerto Plata",
    "La Romana",
    "Higüey",
    "Bonao"
]

BUSINESS_TYPES = [
    "pharmacy",
    "bakery",
    "restaurant",
    "ecommerce",
    "office_supply",
    "hotel",
    "clinic",
    "school"
]

CANALES = ["sales_rep", "whatsapp", "ecommerce", "field_sales"]

# Productos por categoría (nombre, SKU base)
PRODUCTOS_POR_CATEGORIA = {
    "packaging": [
        ("Caja Cartón 10x10", "BOX-CARD-10"),
        ("Caja Cartón 15x15", "BOX-CARD-15"),
        ("Caja Cartón 20x20", "BOX-CARD-20"),
        ("Caja Cartón 25x25", "BOX-CARD-25"),
        ("Caja Plástica Reforzada", "BOX-PLAST-R"),
        ("Bolsa Kraft Pequeña", "BAG-KRAFT-S"),
        ("Bolsa Kraft Mediana", "BAG-KRAFT-M"),
        ("Bolsa Kraft Grande", "BAG-KRAFT-L"),
        ("Cinta Selladora Clara", "TAPE-CLEAR"),
        ("Cinta Selladora Marrón", "TAPE-BROWN"),
    ],
    "labels": [
        ("Etiqueta Adhesiva 25x25", "LAB-ADH-25"),
        ("Etiqueta Adhesiva 40x40", "LAB-ADH-40"),
        ("Etiqueta Adhesiva 50x50", "LAB-ADH-50"),
        ("Etiqueta Térmica 40x30", "LAB-THERM-40"),
        ("Etiqueta Térmica 60x40", "LAB-THERM-60"),
        ("Etiqueta Código Barras", "LAB-BARCODE"),
        ("Etiqueta Fluorescente", "LAB-FLUOR"),
    ],
    "food_service": [
        ("Vaso Biodegradable 8oz", "CUP-BIO-8"),
        ("Vaso Biodegradable 12oz", "CUP-BIO-12"),
        ("Vaso Biodegradable 16oz", "CUP-BIO-16"),
        ("Servilleta Premium Blanca", "NAP-PREM-W"),
        ("Servilleta Premium Colores", "NAP-PREM-C"),
        ("Plato Biodegradable", "PLATE-BIO"),
        ("Cubierto Biodegradable", "CUTL-BIO"),
    ],
    "paper": [
        ("Papel Térmico 80x80", "THERM-80x80"),
        ("Papel Térmico 80x150", "THERM-80x150"),
        ("Tinta para Impresora HP", "INK-HP"),
        ("Tinta para Impresora Canon", "INK-CANON"),
        ("Papel Recibo 80mm", "RECEIPT-80"),
        ("Papel Recibo 58mm", "RECEIPT-58"),
        ("Papel Fotográfico Glossy", "PHOTO-GLOSS"),
    ],
    "cleaning": [
        ("Desengrasante Industrial", "CLEAN-DEGREASER"),
        ("Limpiador Multiusos", "CLEAN-MULTI"),
        ("Desinfectante Concentrado", "CLEAN-DISINFECT"),
        ("Paño Microfibra Azul", "CLOTH-MICRO-B"),
        ("Paño Microfibra Rojo", "CLOTH-MICRO-R"),
        ("Detergente Industrial", "CLEAN-DETERG"),
    ],
    "protective": [
        ("Relleno Protector Papel", "FILL-PAPER"),
        ("Relleno Protector Plástico", "FILL-PLAST"),
        ("Film Stretch 50cm", "WRAP-STRETCH-50"),
        ("Film Stretch 100cm", "WRAP-STRETCH-100"),
        ("Burbuja Protectora", "WRAP-BUBBLE"),
        ("Espuma Protectora", "WRAP-FOAM"),
    ],
}


# ============================================================================
# GENERADOR DE DATOS
# ============================================================================

def generar_productos() -> list:
    """Genera 50 productos distribuidos en las 6 categorías."""
    productos = []
    product_counter = 1
    
    for categoria in CATEGORIAS:
        items_categoria = PRODUCTOS_POR_CATEGORIA[categoria]
        # Distribuir los 50 productos proporcionalmente
        cantidad_por_categoria = 8 if categoria != "labels" else 9  # Ajuste para llegar a 50
        
        for i, (nombre, sku_base) in enumerate(items_categoria[:cantidad_por_categoria]):
            product_id = f"{sku_base.split('-')[0]}-{product_counter:03d}"
            sku = f"{sku_base}-{i+1:02d}"
            margin_pct = round(random.uniform(0.15, 0.45), 2)
            strategic_priority = round(random.uniform(0.3, 1.0), 2)
            
            productos.append(
                Producto(
                    product_id=product_id,
                    sku=sku,
                    name=nombre,
                    category=categoria,
                    margin_pct=margin_pct,
                    strategic_priority=strategic_priority,
                    active=True,
                )
            )
            product_counter += 1
    
    return productos[:50]  # Garantizar exactamente 50


def generar_clientes() -> list:
    """Genera 20 clientes con business types y ciudades variadas."""
    clientes = []
    business_type_idx = 0
    ciudad_idx = 0
    
    for i in range(20):
        customer_id = f"CUST-{i+1:03d}"
        business_type = BUSINESS_TYPES[business_type_idx % len(BUSINESS_TYPES)]
        city = CIUDADES[ciudad_idx % len(CIUDADES)]
        average_order_value = round(random.uniform(500, 3000), 2)
        
        clientes.append(
            Cliente(
                customer_id=customer_id,
                business_type=business_type,
                city=city,
                average_order_value=average_order_value,
            )
        )
        
        business_type_idx += 1
        ciudad_idx += 1
    
    return clientes


def generar_reglas_afinidad(session: Session) -> list:
    """Genera 15+ reglas de afinidad entre categorías con sentido comercial."""
    rules = [
        # PACKAGING → OTHERS
        ("packaging", "labels", 0.9),
        ("packaging", "protective", 0.85),
        ("packaging", "paper", 0.7),
        
        # LABELS → OTHERS
        ("labels", "packaging", 0.88),
        ("labels", "protective", 0.75),
        
        # FOOD_SERVICE → OTHERS
        ("food_service", "packaging", 0.95),
        ("food_service", "labels", 0.8),
        ("food_service", "paper", 0.6),
        
        # PAPER → OTHERS
        ("paper", "packaging", 0.65),
        ("paper", "labels", 0.72),
        ("paper", "cleaning", 0.55),
        
        # CLEANING → OTHERS
        ("cleaning", "protective", 0.7),
        ("cleaning", "packaging", 0.5),
        
        # PROTECTIVE → OTHERS
        ("protective", "packaging", 0.82),
        ("protective", "cleaning", 0.65),
        ("protective", "labels", 0.58),
    ]
    
    reglas = []
    for source, target, weight in rules:
        regla = Regla(
            source_category=source,
            target_category=target,
            weight=weight,
            reason_code="CROSS_SELL_RULE",
            active=True,
        )
        reglas.append(regla)
    
    return reglas


def generar_compras(session: Session, clientes: list, productos: list) -> list:
    """
    Genera historial de compras realista: cada cliente 3-8 compras de 2-3 categorías.
    Crítico para que el motor de recomendaciones funcione bien.
    """
    compras = []
    productos_por_categoria = {}
    
    # Agrupar productos por categoría
    for prod in productos:
        if prod.category not in productos_por_categoria:
            productos_por_categoria[prod.category] = []
        productos_por_categoria[prod.category].append(prod)
    
    for cliente in clientes:
        # Seleccionar 2-3 categorías para este cliente
        categorias_cliente = random.sample(CATEGORIAS, random.randint(2, 3))
        
        # Generar 3-8 compras
        num_compras = random.randint(3, 8)
        
        for _ in range(num_compras):
            # Seleccionar categoría aleatoria del cliente
            categoria = random.choice(categorias_cliente)
            # Seleccionar producto aleatorio de esa categoría
            producto = random.choice(productos_por_categoria[categoria])
            # Cantidad realista
            cantidad = random.randint(1, 20)
            # Canal aleatorio
            canal = random.choice(CANALES)
            
            compra = Compra(
                customer_id=cliente.customer_id,
                product_id=producto.product_id,
                quantity=cantidad,
                channel=canal,
                city=cliente.city,
            )
            compras.append(compra)
    
    return compras


def generar_eventos(session: Session, clientes: list, productos: list) -> list:
    """
    Genera eventos de comportamiento realista:
    - product_view: 5-15 por cliente
    - recommendation_shown: 2-6 por cliente (con UUID de recommendation)
    - recommendation_clicked: 1-3 por cliente (referenciando los recommendation_shown)
    """
    eventos = []
    
    for cliente in clientes:
        # Eventos product_view
        num_views = random.randint(5, 15)
        for _ in range(num_views):
            producto = random.choice(productos)
            evento = Event(
                event_type=EventType.product_view,
                customer_id=cliente.customer_id,
                entity_type="product",
                entity_id=producto.product_id,
                properties={"timestamp_view": datetime.utcnow().isoformat()},
            )
            eventos.append(evento)
        
        # Eventos recommendation_shown (con UUID simulados de recommendation)
        recommendation_ids = [str(uuid.uuid4()) for _ in range(random.randint(2, 6))]
        for rec_id in recommendation_ids:
            evento = Event(
                event_type=EventType.recommendation_shown,
                customer_id=cliente.customer_id,
                entity_type="recommendation",
                entity_id=rec_id,
                properties={
                    "slot": "hero",
                    "page_type": "homepage",
                    "item_count": random.randint(3, 5),
                },
            )
            eventos.append(evento)
        
        # Eventos recommendation_clicked (1-3, referenciando los recommendation_shown)
        num_clicks = random.randint(1, min(3, len(recommendation_ids)))
        recommendation_ids_sample = random.sample(recommendation_ids, num_clicks)
        for rec_id in recommendation_ids_sample:
            producto = random.choice(productos)
            evento = Event(
                event_type=EventType.recommendation_clicked,
                customer_id=cliente.customer_id,
                entity_type="recommendation",
                entity_id=rec_id,
                properties={
                    "product_id": producto.product_id,
                    "rank_position": random.randint(1, 5),
                    "slot": "hero",
                    "page_type": "homepage",
                },
            )
            eventos.append(evento)
    
    return eventos


# ============================================================================
# MAIN
# ============================================================================

def seed_demo() -> None:
    """Ejecuta la carga masiva de datos de demostración."""
    print("\n" + "=" * 70)
    print("INICIANDO CARGA DE DATOS DE DEMOSTRACIÓN")
    print("=" * 70 + "\n")
    
    init_db()
    
    with Session(engine) as session:
        # 1. GENERAR Y INSERTAR PRODUCTOS
        print("📦 Generando 50 productos...")
        productos = generar_productos()
        contador_productos = 0
        for producto in productos:
            _ensure_product(session, producto)
            contador_productos += 1
        
        session.commit()
        print(f"   ✓ Insertados {contador_productos} productos\n")
        
        # 2. GENERAR Y INSERTAR CLIENTES
        print("👥 Generando 20 clientes...")
        clientes = generar_clientes()
        contador_clientes = 0
        for cliente in clientes:
            _ensure_customer(session, cliente)
            contador_clientes += 1
        
        session.commit()
        print(f"   ✓ Insertados {contador_clientes} clientes\n")
        
        # 3. GENERAR Y INSERTAR REGLAS DE AFINIDAD
        print("🔗 Generando reglas de afinidad...")
        reglas = generar_reglas_afinidad(session)
        contador_reglas = 0
        for regla in reglas:
            _ensure_rule(session, regla)
            contador_reglas += 1
        
        session.commit()
        print(f"   ✓ Insertadas {contador_reglas} reglas de afinidad\n")
        
        # 4. GENERAR E INSERTAR COMPRAS
        print("🛒 Generando historial de compras...")
        compras = generar_compras(session, clientes, productos)
        contador_compras = 0
        for compra in compras:
            _ensure_purchase(session, compra)
            contador_compras += 1
        
        session.commit()
        print(f"   ✓ Insertadas {contador_compras} compras\n")
        
        # 5. GENERAR E INSERTAR EVENTOS
        print("📊 Generando eventos de comportamiento...")
        eventos = generar_eventos(session, clientes, productos)
        contador_eventos = 0
        for evento in eventos:
            _ensure_event(session, evento)
            contador_eventos += 1
        
        session.commit()
        print(f"   ✓ Insertados {contador_eventos} eventos\n")
        
        # RESUMEN FINAL
        print("=" * 70)
        print("RESUMEN DE CARGA")
        print("=" * 70)
        print(f"  Productos:           {contador_productos:>6}")
        print(f"  Clientes:            {contador_clientes:>6}")
        print(f"  Reglas de Afinidad:  {contador_reglas:>6}")
        print(f"  Compras:             {contador_compras:>6}")
        print(f"  Eventos:             {contador_eventos:>6}")
        print("=" * 70)
        print("\n✅ Base de datos cargada correctamente con datos de demostración.\n")


if __name__ == "__main__":
    seed_demo()
