from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models import Compra, Cliente, Producto

router = APIRouter(prefix="/customers", tags=["customers"])
users_router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
@users_router.get("")
def list_customers(session: Session = Depends(get_session)):
	return session.exec(select(Cliente)).all()


@router.get("/{customer_id}")
@users_router.get("/{customer_id}")
def get_customer(customer_id: str, session: Session = Depends(get_session)):
	customer = session.get(Cliente, customer_id)
	if not customer:
		raise HTTPException(status_code=404, detail="Customer not found")

	return customer


@router.get("/{customer_id}/history")
@users_router.get("/{customer_id}/history")
def get_customer_history(customer_id: str, session: Session = Depends(get_session)):
	customer = session.get(Cliente, customer_id)
	if not customer:
		raise HTTPException(status_code=404, detail="Customer not found")

	purchases = session.exec(select(Compra).where(Compra.customer_id == customer_id)).all()
	products = {product.product_id: product for product in session.exec(select(Producto)).all()}

	return {
		"customer_id": customer_id,
		"purchases": [
			{
				"purchase_id": purchase.purchase_id,
				"product_id": purchase.product_id,
				"product_name": products.get(purchase.product_id).name if purchase.product_id in products else None,
				"category": products.get(purchase.product_id).category if purchase.product_id in products else None,
				"quantity": purchase.quantity,
				"channel": purchase.channel,
				"city": purchase.city,
				"purchased_at": purchase.purchased_at.isoformat() if purchase.purchased_at else None,
			}
			for purchase in purchases
		],
	}