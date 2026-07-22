from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.models.usuario import UserRole
from app.services.admin import (
    create_rule,
    get_rule,
    get_system_status,
    list_rules,
    serialize_rule,
    update_rule,
)
from app.services.auth import require_role
from app.services.campaigns import (
    create_campaign,
    create_offer,
    list_campaigns,
    list_offers,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/rules")
def list_rules_endpoint(
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.viewer)),
) -> list[dict]:
    return list_rules(session)


@router.get("/rules/{rule_id}")
def get_rule_endpoint(
    rule_id: int,
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.viewer)),
) -> dict:
    rule = get_rule(session, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return serialize_rule(rule)


@router.post("/rules", status_code=201)
def create_rule_endpoint(
    payload: dict,
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.admin)),
) -> dict:
    try:
        return create_rule(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/rules/{rule_id}")
def update_rule_endpoint(
    rule_id: int,
    payload: dict,
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.admin)),
) -> dict:
    rule = update_rule(session, rule_id, payload)
    if rule is None:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return serialize_rule(rule)


@router.get("/status")
def system_status_endpoint(
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.viewer)),
) -> dict:
    return get_system_status(session)


@router.get("/campaigns")
def list_campaigns_endpoint(
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.viewer)),
) -> list[dict]:
    return list_campaigns(session)


@router.post("/campaigns", status_code=201)
def create_campaign_endpoint(
    payload: dict,
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.admin)),
) -> dict:
    try:
        return create_campaign(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/offers")
def list_offers_endpoint(
    campaign_id: int | None = None,
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.viewer)),
) -> list[dict]:
    return list_offers(session, campaign_id=campaign_id)


@router.post("/offers", status_code=201)
def create_offer_endpoint(
    payload: dict,
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.admin)),
) -> dict:
    try:
        return create_offer(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integrations/sync/{entity}")
def trigger_integration_sync(
    entity: str,
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.admin)),
) -> dict:
    if entity not in ["catalog", "customers", "inventory"]:
        raise HTTPException(status_code=400, detail="Invalid sync entity")
    # Here we would trigger the sync service or a background worker
    return {"status": "ok", "message": f"Sync process started for {entity}"}


@router.get("/integrations/status")
def get_integrations_status(
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.admin)),
) -> dict:
    return {
        "erp": {"status": "connected"},
        "crm": {"status": "connected"},
        "whatsapp": {"status": "pending_config"}
    }

from sqlalchemy import text
from app.models.audit import AuditLog

@router.get("/diagnostics")
def system_diagnostics_endpoint(
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.super_admin)),
) -> dict:
    try:
        session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "database": db_status,
        "environment": "production",
        "cache": "redis_mocked",
        "version": "0.3.0",
        "integrations": get_integrations_status(session, _user)
    }


@router.get("/audit")
def list_audit_logs_endpoint(
    limit: int = 50,
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.super_admin)),
) -> list[dict]:
    # Query de sqlmodel
    from sqlmodel import select
    logs = session.exec(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "target_resource": log.target_resource,
            "details": log.details,
            "created_at": log.created_at.isoformat()
        } for log in logs
    ]
