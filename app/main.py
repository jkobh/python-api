from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.database import database
from app.repositories.errors import ConflictError, NotFoundError, RepositoryError
from app.routers import kaffeebohnen, maschinen, standorte

type ErrorHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]

ERROR_STATUS: frozendict[type[RepositoryError], int] = frozendict(
    {
        NotFoundError: status.HTTP_404_NOT_FOUND,
        ConflictError: status.HTTP_409_CONFLICT,
    }
)


def build_error_handler(http_status: int) -> ErrorHandler:
    async def handle(_: Request, error: Exception) -> JSONResponse:
        return JSONResponse(status_code=http_status, content={"detail": str(error)})

    return handle


def register_error_handlers(app: FastAPI) -> None:
    for error_type, http_status in ERROR_STATUS.items():
        app.add_exception_handler(error_type, build_error_handler(http_status))


def create_app(initialize_database: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        if initialize_database:
            database.create_schema()
        yield

    app = FastAPI(title="Coffee Machine API", version="0.1.0", lifespan=lifespan)

    app.include_router(standorte.router)
    app.include_router(maschinen.router)
    app.include_router(kaffeebohnen.router)
    register_error_handlers(app)

    return app


app = create_app()
