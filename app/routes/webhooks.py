import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.db.session import get_session
from app.models.integration import IntegrationLog

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

    # Podría parsearse el tipo de evento del body según el provider, 
    # por simplicidad lo seteamos como 'webhook_event' genérico o extraído si existe.
    event_type = body_json.get("type", "unknown_event") if isinstance(body_json, dict) else "unknown_event"

    log_entry = IntegrationLog(
        provider=provider,
        event_type=event_type,
        payload=payload_str,
        status="processed" # Para simular que lo encolamos o procesamos
    )
    
    session.add(log_entry)
    session.commit()
    session.refresh(log_entry)
    
    return {"status": "ok", "message": f"Event received from {provider}", "id": log_entry.id}
