import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Almacena el Request ID de la petición actual
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class TraceabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Tomar el ID provisto por un balanceador de carga o generarlo
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Guardarlo en la variable de contexto para esta petición
        token = request_id_var.set(request_id)
        
        try:
            response = await call_next(request)
            # Retornarlo al cliente en los headers
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)

def get_request_id() -> str:
    """Devuelve el ID de la petición actual si existe."""
    return request_id_var.get()
