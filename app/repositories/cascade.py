import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import Kaffeebohne, Maschine


def active_maschinen_ids(session: Session, standort_id: uuid.UUID) -> list[uuid.UUID]:
    statement = select(Maschine.id).where(
        Maschine.standort_id == standort_id, Maschine.deleted_at.is_(None)
    )
    return list(session.scalars(statement).all())


def soft_delete_kaffeebohnen(
    session: Session, maschinen_ids: Sequence[uuid.UUID], deleted_at: datetime
) -> None:
    if not maschinen_ids:
        return
    session.execute(
        update(Kaffeebohne)
        .where(Kaffeebohne.maschine_id.in_(maschinen_ids), Kaffeebohne.deleted_at.is_(None))
        .values(
            deleted_at=deleted_at,
            version=Kaffeebohne.version + 1,
            updated_at=func.now(),
        )
        .execution_options(synchronize_session=False)
    )


def soft_delete_maschinen(
    session: Session, maschinen_ids: Sequence[uuid.UUID], deleted_at: datetime
) -> None:
    if not maschinen_ids:
        return
    session.execute(
        update(Maschine)
        .where(Maschine.id.in_(maschinen_ids), Maschine.deleted_at.is_(None))
        .values(
            deleted_at=deleted_at,
            version=Maschine.version + 1,
            updated_at=func.now(),
        )
        .execution_options(synchronize_session=False)
    )
