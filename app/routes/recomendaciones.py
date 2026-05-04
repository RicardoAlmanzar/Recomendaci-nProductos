from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.engine.scorer import build_recommendation_payload, build_recommendations
from app.models import Compra, Cliente, Producto, Regla, RecommendationRequest

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("")
def recommend(input_data: RecommendationRequest, session: Session = Depends(get_session)):
	customer = session.get(Cliente, input_data.customer_id)
	if not customer:
		raise HTTPException(status_code=404, detail="Customer not found")

	catalog = session.exec(select(Producto)).all()
	affinity_rules = session.exec(select(Regla)).all()
	purchases = session.exec(select(Compra).where(Compra.customer_id == input_data.customer_id)).all()

	recommendations = build_recommendations(
		customer=customer,
		catalog=catalog,
		affinity_rules=affinity_rules,
		purchases=purchases,
		limit=input_data.limit,
	)

	return build_recommendation_payload(input_data.customer_id, recommendations)