import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.db.session import get_session
from app.models.integration import IntegrationLog

from app.core.queue import task_queue

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/{provider}/events")
async def receive_webhook_event(
    provider: str,
    request: Request,
    session: Session = Depends(get_session)
) -> dict:
    if provider not in ["erp", "crm", "whatsapp"]:
        raise HTTPException(status_code=400, detail="Invalid provider")
    
    try:
        body_json = await request.json()
        payload_str = json.dumps(body_json)
    except Exception:
        body_bytes = await request.body()
        payload_str = body_bytes.decode('utf-8') or "{}"

    event_type = body_json.get("type", "unknown_event") if isinstance(body_json, dict) else "unknown_event"

    from app.core.tenant import get_tenant_id
    
    log_entry = IntegrationLog(
        provider=provider,
        event_type=event_type,
        payload=payload_str,
        status="enqueued",
        tenant_id=get_tenant_id()
    )
    
    session.add(log_entry)
    session.commit()
    session.refresh(log_entry)
    
    # Encolar la tarea pesada en background usando RQ
    task_queue.enqueue(
        "app.worker.process_webhook_event",
        args=(provider, event_type, payload_str, log_entry.id),
        job_timeout="10m"
    )
    
    return {"status": "accepted", "message": f"Event queued for {provider}", "id": log_entry.id}
