from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Campana(SQLModel, table=True):
    __tablename__ = "campaigns"

    campaign_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    channel: str = Field(max_length=50, index=True)
    active: bool = Field(default=True)
    starts_at: Optional[datetime] = Field(default=None)
    ends_at: Optional[datetime] = Field(default=None)
