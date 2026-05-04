from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Compra(SQLModel, table=True):
	__tablename__ = "purchases"

	purchase_id: Optional[int] = Field(default=None, primary_key=True)
	customer_id: str = Field(foreign_key="customers.customer_id", max_length=50)
	product_id: str = Field(foreign_key="products.product_id", max_length=50)
	quantity: float = Field(default=1)
	purchased_at: datetime = Field(default_factory=datetime.utcnow)
	channel: str | None = Field(default=None, max_length=50)
	city: str | None = Field(default=None, max_length=100)