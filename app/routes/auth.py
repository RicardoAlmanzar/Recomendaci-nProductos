from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.services.auth import login_with_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(payload: dict, session: Session = Depends(get_session)) -> dict:
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=422, detail="Campo email requerido")
    try:
        return login_with_email(session, str(email))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
