"""Autenticación JWT y autorización RBAC — Módulo 4."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.usuario import AdminUser, UserRole

JWT_SECRET = os.getenv("JWT_SECRET", "dev-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
ADMIN_AUTH_DISABLED = os.getenv("ADMIN_AUTH_DISABLED", "true").lower() in {"1", "true", "yes"}

ROLE_RANK = {
    UserRole.viewer: 1,
    UserRole.operator: 2,
    UserRole.analyst: 3,
    UserRole.admin: 4,
    UserRole.super_admin: 5,
}

bearer_scheme = HTTPBearer(auto_error=False)


def ensure_default_admin(session: Session) -> None:
    existing = session.exec(
        select(AdminUser).where(AdminUser.email == "admin@gjs.local")
    ).first()
    if existing is None:
        session.add(
            AdminUser(
                email="admin@gjs.local",
                role=UserRole.super_admin,
                active=True,
            )
        )
        session.commit()


def login_with_email(session: Session, email: str) -> dict:
    user = session.exec(
        select(AdminUser).where(AdminUser.email == email, AdminUser.active.is_(True))
    ).first()
    if user is None:
        raise ValueError("Credenciales inválidas")

    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_MINUTES * 60,
        "user": {
            "email": user.email,
            "role": user.role.value,
        },
    }


def create_access_token(user: AdminUser) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.email,
        "role": user.role.value,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise ValueError("Token inválido o expirado") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> AdminUser | None:
    if ADMIN_AUTH_DISABLED:
        return None
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    email = payload.get("sub")
    user = session.exec(
        select(AdminUser).where(AdminUser.email == email, AdminUser.active.is_(True))
    ).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autorizado")
    return user


def require_role(min_role: UserRole):
    def dependency(user: AdminUser | None = Depends(get_current_user)) -> AdminUser | None:
        if ADMIN_AUTH_DISABLED:
            return None
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
        if ROLE_RANK[user.role] < ROLE_RANK[min_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return user

    return dependency
