from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Optional

# Almacena el Tenant ID de la petición actual
tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Tomar el Tenant ID provisto por los headers (para GJS Core o Paraiso.do)
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # Guardarlo en la variable de contexto para esta petición
        token = tenant_id_var.set(tenant_id)
        
        try:
            response = await call_next(request)
            return response
        finally:
            tenant_id_var.reset(token)

def get_tenant_id() -> Optional[str]:
    """Devuelve el Tenant ID de la petición actual si existe."""
    return tenant_id_var.get()
