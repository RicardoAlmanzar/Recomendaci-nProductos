from fastapi import APIRouter, Depends, Query
from sqlmodel import SQLModel, Session, select

from app.db.session import get_session
from app.models import Producto

router = APIRouter(prefix="/products", tags=["products"])


class ProductSearchResult(SQLModel):
    product_id: str
    sku: str
    name: str
    category: str


@router.get("/search", response_model=list[ProductSearchResult])
def search_products(
    q: str = Query(..., min_length=1, description="Texto a buscar en el nombre del producto"),
    session: Session = Depends(get_session),
) -> list[ProductSearchResult]:
    term = q.strip()
    if not term:
        return []

    products = session.exec(
        select(Producto)
        .where(Producto.active == True)  # noqa: E712
        .where(Producto.name.ilike(f"%{term}%"))  # type: ignore[union-attr]
        .order_by(Producto.name)
    ).all()

    return [
        ProductSearchResult(
            product_id=product.product_id,
            sku=product.sku,
            name=product.name,
            category=product.category,
        )
        for product in products
    ]
