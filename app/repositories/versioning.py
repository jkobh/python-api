import uuid
from typing import Any

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.models import Entity
from app.repositories.errors import VersionConflictError


def update_with_version(
    session: Session,
    model: type[Entity],
    entity_id: uuid.UUID,
    version: int,
    values: dict[str, Any],
) -> None:
    statement = (
        update(model)
        .where(model.id == entity_id, model.deleted_at.is_(None), model.version == version)
        .values(**values, version=model.version + 1, updated_at=func.now())
        .returning(model.id)
        .execution_options(synchronize_session=False)
    )
    if session.execute(statement).scalar_one_or_none() is None:
        raise VersionConflictError(model.__tablename__, entity_id)
