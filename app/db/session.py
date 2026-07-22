from sqlalchemy.engine.url import make_url
from pydantic import Field
from pydantic.aliases import AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.models.event import EventType
from app.models.integration import IntegrationLog, ExternalMapping
from app.models.audit import AuditLog


class Settings(BaseSettings):
    supabase_database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_DATABASE_URL", "DATABASE_URL")
    )
    supabase_pooler_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_POOLER_URL", "SUPABASE_POOL_URL")
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

database_url_value = settings.supabase_pooler_url or settings.supabase_database_url
if not database_url_value:
    raise RuntimeError("Define SUPABASE_POOLER_URL o SUPABASE_DATABASE_URL en .env")

database_url = make_url(database_url_value)
connect_args = {"check_same_thread": False} if database_url.get_backend_name() == "sqlite" else {}
engine = create_engine(database_url_value, echo=True, connect_args=connect_args)


def _ensure_postgres_event_enum_values() -> None:
    if database_url.get_backend_name() != "postgresql":
        return

    with engine.begin() as connection:
        for event_type in EventType:
            connection.execute(
                text(f"ALTER TYPE eventtype ADD VALUE IF NOT EXISTS '{event_type.value}'")
            )


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_postgres_event_enum_values()


def get_session():
    with Session(engine) as session:
        yield session
