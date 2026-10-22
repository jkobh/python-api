from collections.abc import Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_session
from app.main import create_app

TEST_DATABASE_URL = "postgresql+psycopg://coffee:coffee@localhost:5432/coffee_machine_test"
TEST_DATABASE_NAME = "coffee_machine_test"
ADMIN_DATABASE_URL = "postgresql://coffee:coffee@localhost:5432/coffee_machine"


def ensure_test_database() -> None:
    with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
        exists = connection.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DATABASE_NAME,)
        ).fetchone()
        if exists is None:
            connection.execute(f'CREATE DATABASE "{TEST_DATABASE_NAME}"')


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    try:
        ensure_test_database()
    except psycopg.Error as error:
        pytest.exit(f"PostgreSQL nicht erreichbar: {error}", returncode=1)
    test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db_session:
        yield db_session
        db_session.rollback()


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Iterator[Session]:
        with factory() as db_session:
            yield db_session

    application = create_app(initialize_database=False)
    application.dependency_overrides[get_session] = override_session
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_tables(engine: Engine) -> Iterator[None]:
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE kaffeebohnen, maschinen, standorte RESTART IDENTITY CASCADE")
        )
    yield