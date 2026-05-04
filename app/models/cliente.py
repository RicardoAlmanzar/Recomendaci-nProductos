from datetime import datetime

from sqlmodel import Field, SQLModel


class Cliente(SQLModel, table=True):
	__tablename__ = "customers"

	customer_id: str = Field(primary_key=True, max_length=50)
	business_type: str = Field(max_length=100)
	city: str = Field(max_length=100)
	average_order_value: float = Field(default=0)
	created_at: datetime = Field(default_factory=datetime.utcnow)