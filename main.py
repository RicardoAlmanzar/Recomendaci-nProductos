from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import init_db
from app.routes.auth import router as auth_router
from app.routes.clientes import router as customers_router, users_router
from app.routes.recomendaciones import router as recommendations_router
from app.routes.events import router as events_router
from app.routes.metrics import router as metrics_router
from app.routes.productos import router as products_router
from app.routes.admin import router as admin_router
from app.services.auth import ensure_default_admin
from app.db.session import engine
from sqlmodel import Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        ensure_default_admin(session)
    yield


from app.routes.webhooks import router as webhooks_router

app = FastAPI(lifespan=lifespan)

# CORS Allowlist básica (Módulo 10)
# En producción esto vendría de variables de entorno.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://miapp.gjs.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Cabeceras de seguridad básicas (Helmet-like)
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(customers_router)
app.include_router(users_router)
app.include_router(recommendations_router)
app.include_router(events_router)
app.include_router(metrics_router)
app.include_router(products_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(webhooks_router)


@app.get("/")
def read_root():
    return {"message": "Motor de Recomendaciones listo"}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "recommendation-engine",
        "version": "0.3.0",
    }


@app.get("/readiness")
def readiness_check():
    from app.db.session import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Database not ready: {str(e)}")
