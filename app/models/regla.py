from typing import Optional

from sqlmodel import Field, SQLModel


class Regla(SQLModel, table=True):
	__tablename__ = "affinity_rules"

	rule_id: Optional[int] = Field(default=None, primary_key=True)
	source_category: str = Field(max_length=100, index=True)
	target_category: str = Field(max_length=100, index=True)
	weight: float = Field(default=0)
	reason_code: str = Field(max_length=100)
	active: bool = Field(default=True)