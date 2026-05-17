from datetime import datetime, timedelta
from sqlmodel import Session, select, func
from app.models.compra import Compra
from app.models.producto import Producto

def get_popularity_scores(session: Session, window_days: int = 90) -> dict[str, float]:
    """
    Calcula scores de popularidad normalizados (0 a 1) para productos activos
    basados en la cantidad de veces que aparecen en las compras de los últimos N días.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=window_days)
    
    # Contar ocurrencias por producto en compras recientes
    stmt = (
        select(Compra.product_id, func.count(Compra.product_id).label("count"))
        .join(Producto, Compra.product_id == Producto.product_id)
        .where(Producto.active == True)
        .where(Compra.purchased_at >= cutoff_date)
        .group_by(Compra.product_id)
    )
    
    results = session.exec(stmt).all()
    
    if not results:
        return {}
        
    counts = {product_id: count for product_id, count in results}
    max_count = max(counts.values())
    
    if max_count == 0:
        return {}
        
    # Normalizar entre 0 y 1
    return {product_id: count / max_count for product_id, count in counts.items()}


def get_popular_product_ids(
    session: Session,
    limit: int,
    category: str | None = None,
    window_days: int = 90,
) -> list[str]:
    """Retorna product_ids ordenados por frecuencia de compra (DESC).

    Usado por candidates.py para armar el pool cold-start con productos
    que tienen demanda real, no solo strategic_priority alta.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=window_days)

    stmt = (
        select(Compra.product_id)
        .join(Producto, Compra.product_id == Producto.product_id)
        .where(Producto.active == True)  # noqa: E712
        .where(Compra.purchased_at >= cutoff_date)
    )
    if category:
        stmt = stmt.where(Producto.category == category)

    stmt = (
        stmt.group_by(Compra.product_id)
        .order_by(func.count(Compra.product_id).desc())
        .limit(limit)
    )

    return list(session.exec(stmt).all())
