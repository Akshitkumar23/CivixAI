"""
PostgreSQL 16 & pgvector Driver Runtime Tests.
Executed in .github/workflows/postgres_runtime.yml.
Validates PostgreSQL dialect compatibility, pgvector integration, and transaction semantics.
Conditionally skips if PostgreSQL is not reachable in the local environment.
"""
import os
import pytest
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

POSTGRES_TEST_URL = os.getenv(
    "CIVIX_POSTGRES_TEST_URL",
    os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/civix_test")
)


def is_postgres_available() -> bool:
    if not POSTGRES_TEST_URL.startswith(("postgresql://", "postgresql+psycopg2://", "postgres://")):
        return False
    try:
        engine = create_engine(POSTGRES_TEST_URL, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return True
    except Exception:
        return False


POSTGRES_AVAILABLE = is_postgres_available()


@pytest.mark.skipif(
    not POSTGRES_AVAILABLE,
    reason="BLOCKED: PostgreSQL 16 container not reachable on port 5432. Active only in CI with pgvector service container."
)
class TestPostgresRuntime:
    """Live PostgreSQL runtime tests."""

    @pytest.fixture(scope="class")
    def pg_engine(self):
        engine = create_engine(POSTGRES_TEST_URL)
        yield engine
        engine.dispose()

    def test_postgres_version_and_pgvector(self, pg_engine):
        with pg_engine.connect() as conn:
            res = conn.execute(text("SELECT version();")).fetchone()
            assert "PostgreSQL" in res[0]

            # Verify pgvector extension
            vec = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';")).fetchone()
            assert vec is not None

    def test_postgres_schema_creation_and_parity(self, pg_engine):
        from services.core.database.models import Base
        Base.metadata.create_all(bind=pg_engine)

        inspector = inspect(pg_engine)
        tables = inspector.get_table_names()
        assert "schemes" in tables
        assert "eligibility_rules" in tables
        assert "rag_chunks" in tables

    def test_postgres_transaction_rollback(self, pg_engine):
        Session = sessionmaker(bind=pg_engine)
        session = Session()
        try:
            session.execute(text("CREATE TEMPORARY TABLE test_rollback (id serial primary key, val text);"))
            session.execute(text("INSERT INTO test_rollback (val) VALUES ('committed');"))
            session.commit()

            # Attempt failing transaction
            try:
                session.execute(text("INSERT INTO test_rollback (id, val) VALUES (1, 'conflict');"))
                session.commit()
            except Exception:
                session.rollback()

            # Verify previous data remains intact
            rows = session.execute(text("SELECT val FROM test_rollback;")).fetchall()
            assert len(rows) == 1
            assert rows[0][0] == "committed"
        finally:
            session.close()
