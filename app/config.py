from dataclasses import dataclass
from os import getenv

DEFAULT_DATABASE_URL = "postgresql+psycopg://coffee:coffee@localhost:5432/coffee_machine"
DEFAULT_TEST_DATABASE_URL = "postgresql+psycopg://coffee:coffee@localhost:5432/coffee_machine_test"


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    test_database_url: str = DEFAULT_TEST_DATABASE_URL

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            database_url=getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
            test_database_url=getenv("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL),
        )
