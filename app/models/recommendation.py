from typing import List

from sqlmodel import SQLModel


class RecommendationRequest(SQLModel):
    customer_id: str
    limit: int = 5


class RecommendationItem(SQLModel):
    product_id: str
    sku: str
    name: str
    score: float
    reason_codes: List[str]


class RecommendationResponse(SQLModel):
    customer_id: str
    generated_at: str
    recommendations: List[RecommendationItem]