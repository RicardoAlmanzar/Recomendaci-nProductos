from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class IntegrationLog(SQLModel, table=True):
    __tablename__ = "integration_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(index=True)
    event_type: str
    payload: str
    status: str = Field(default="pending", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExternalMapping(SQLModel, table=True):
    __tablename__ = "external_mappings"

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(index=True)
    external_id: str = Field(index=True)
    internal_id: str = Field(index=True)
    provider: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
