from typing import Optional

from sqlmodel import Field, SQLModel


class Oferta(SQLModel, table=True):
    __tablename__ = "offers"

    offer_id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaigns.campaign_id", index=True)
    product_id: str = Field(max_length=50, index=True)
    extra_score: float = Field(default=0.0)
    active: bool = Field(default=True)
