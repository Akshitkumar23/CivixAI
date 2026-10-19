import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SQLITE_PATH = DATA_DIR / "civix.db"

# Ensure data dir exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

# Handle postgres:// legacy prefix if provided by older cloud hosts
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

def get_engine():
    return engine

def init_db():
    from .models import Base
    from services.core.discovery.models import RawDiscoveryRecord, ProgrammeDiscovery
    Base.metadata.create_all(bind=engine)
    # Ensure newly added columns exist in existing databases
    with engine.connect() as conn:
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            if "rag_chunks" in table_names:
                cols = {c["name"] for c in inspector.get_columns("rag_chunks")}
                if "generation_id" not in cols:
                    conn.execute(text("ALTER TABLE rag_chunks ADD COLUMN generation_id VARCHAR(128)"))
                if "generation_status" not in cols:
                    conn.execute(text("ALTER TABLE rag_chunks ADD COLUMN generation_status VARCHAR(32) DEFAULT 'active'"))
            if "rag_documents" in table_names:
                cols = {c["name"] for c in inspector.get_columns("rag_documents")}
                if "generation_id" not in cols:
                    conn.execute(text("ALTER TABLE rag_documents ADD COLUMN generation_id VARCHAR(128)"))
                if "generation_status" not in cols:
                    conn.execute(text("ALTER TABLE rag_documents ADD COLUMN generation_status VARCHAR(32) DEFAULT 'active'"))
            if "rag_index_runs" in table_names:
                cols = {c["name"] for c in inspector.get_columns("rag_index_runs")}
                if "generation_id" not in cols:
                    conn.execute(text("ALTER TABLE rag_index_runs ADD COLUMN generation_id VARCHAR(128)"))
                if "generation_status" not in cols:
                    conn.execute(text("ALTER TABLE rag_index_runs ADD COLUMN generation_status VARCHAR(32) DEFAULT 'staging'"))
            conn.commit()
        except Exception:
            pass
