"""
Shared test fixtures.

Tests run against a throwaway SQLite database, not the Postgres instance
the app targets in dev/production (see docker-compose.yml). This is a
deliberate, standard trade-off: it keeps the test suite fast and
dependency-free (no Postgres server required to run `pytest`), while the
Alembic migration itself (alembic/versions/) is what's actually applied
to Postgres - see docs/architecture.md. The ORM layer (SQLAlchemy) is the
same in both cases, so this still exercises real model/relationship/
service behavior, just not Postgres-specific SQL.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
