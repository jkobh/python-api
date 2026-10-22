from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.database import Base, get_session
from app.main import create_app

SETTINGS = Settings.from_environment()
TEST_DATABASE_NAME: str = make_url(SETTINGS.test_database_url).database or "coffee_machine_test"


def create_test_database() -> Engine:
    admin_engine = create_engine(
        make_url(SETTINGS.database_url).set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE_NAME}"'))
    return admin_engine


def drop_test_database(admin_engine: Engine) -> None:
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DATABASE_NAME}" WITH (FORCE)'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    try:
        admin_engine = create_test_database()
    except SQLAlchemyError as error:
        pytest.exit(f"PostgreSQL nicht erreichbar: {error}", returncode=1)
    test_engine = create_engine(SETTINGS.test_database_url, pool_pre_ping=True)
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()
    drop_test_database(admin_engine)


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
