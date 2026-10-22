from collections.abc import Iterator
from importlib import import_module

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.base import Base
from app.config import Settings

__all__ = ["Base", "Database", "database", "get_session"]


class Database:
    def __init__(self, url: str) -> None:
        self.engine: Engine = create_engine(url, pool_pre_ping=True)
        self.session_factory: sessionmaker[Session] = sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    def create_schema(self) -> None:
        import_module("app.models")
        Base.metadata.create_all(self.engine)

    def dispose(self) -> None:
        self.engine.dispose()

    def open_session(self) -> Iterator[Session]:
        with self.session_factory() as session:
            yield session


database = Database(Settings.from_environment().database_url)


def get_session() -> Iterator[Session]:
    yield from database.open_session()
