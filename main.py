from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import init_db
from app.routes.clientes import router as customers_router, users_router
from app.routes.recomendaciones import router as recommendations_router
from app.routes.events import router as events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(customers_router)
app.include_router(users_router)
app.include_router(recommendations_router)
app.include_router(events_router)


@app.get("/")
def read_root():
    return {"message": "Motor de Recomendaciones listo"}
