from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Session


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    action: str = Field(index=True)
    target_resource: str
    details: str
    tenant_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

def create_audit_log(session: Session, action: str, target_resource: str, details: str, user_id: int = None):
    from app.core.tenant import get_tenant_id
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        target_resource=target_resource,
        details=details,
        tenant_id=get_tenant_id()
    )
    session.add(log_entry)
    session.commit()
    return log_entry
