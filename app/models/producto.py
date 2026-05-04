from datetime import datetime

from sqlmodel import Field, SQLModel


class Producto(SQLModel, table=True):
	__tablename__ = "products"

	product_id: str = Field(primary_key=True, max_length=50)
	sku: str = Field(max_length=100, index=True, unique=True)
	name: str = Field(max_length=255)
	category: str = Field(max_length=100, index=True)
	margin_pct: float = Field(default=0)
	strategic_priority: float = Field(default=0)
	active: bool = Field(default=True)
	created_at: datetime = Field(default_factory=datetime.utcnow)