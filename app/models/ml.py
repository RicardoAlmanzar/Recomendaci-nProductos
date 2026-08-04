from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class FeatureSnapshot(SQLModel, table=True):
    """
    Guarda el estado de las features de un cliente o producto 
    en un momento dado, para luego entrenar el modelo.
    """
    __tablename__ = "ml_feature_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(index=True) # e.g. "customer", "product"
    entity_id: str = Field(index=True)
    features_json: str # JSON con vector de features
    snapshot_date: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: Optional[str] = Field(default=None, index=True)

class TrainingRun(SQLModel, table=True):
    """
    Audita cada ejecución de entrenamiento del modelo de ML.
    """
    __tablename__ = "ml_training_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    model_version: str = Field(index=True)
    status: str = Field(default="started") # started, completed, failed
    metrics_json: Optional[str] = None # e.g. {"accuracy": 0.85, "loss": 0.12}
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
