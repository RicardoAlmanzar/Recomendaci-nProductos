"""
app/routes/metrics.py — Módulo 9: Endpoint de métricas de evaluación.

Proporciona el endpoint GET /admin/metrics para consultar el rendimiento del motor
de recomendaciones (CTR, tasas de conversión y productos populares).
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db.session import get_session
from app.models.usuario import UserRole
from app.services.auth import require_role
from app.services.metrics import build_metrics_summary, compute_metrics

# Estilo estándar del repo para routers
router = APIRouter(prefix="/admin/metrics", tags=["admin", "metrics"])


@router.get("")
def get_admin_metrics(
    days: int = Query(default=30, ge=1, le=365, description="Ventana de tiempo en días para calcular las métricas"),
    top_n: int = Query(default=10, ge=1, le=100, description="Número de productos top a incluir en el reporte"),
    session: Session = Depends(get_session),
    _user=Depends(require_role(UserRole.viewer)),
) -> dict:
    """
    Obtiene el reporte de evaluación y métricas de rendimiento para el administrador.
    Retorna CTR, tasa de conversión directa y los productos recomendados más populares.
    """
    # TODO: agregar autenticación antes de pasar a producción
    return build_metrics_summary(db=session, window_days=days, top_n=top_n)
