import os
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, create_engine, Field

# Use in-memory SQLite — wiped on every restart, no file saved
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

class AssessmentSession(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    filename: str
    original_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

def init_db():
    SQLModel.metadata.create_all(engine)
