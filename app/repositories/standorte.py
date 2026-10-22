import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update as sql_update
from sqlalchemy.orm import Session

from app.models import Standort
from app.repositories import cascade
from app.repositories.errors import NotFoundError
from app.repositories.versioning import update_with_version
from app.schemas import StandortCreate, StandortUpdate


def create(session: Session, data: StandortCreate) -> Standort:
    standort = Standort(name=data.name, ort=data.ort)
    session.add(standort)
    session.commit()
    session.refresh(standort)
    return standort


def list_all(session: Session, name: str | None, ort: str | None) -> list[Standort]:
    statement: Select[Standort] = select(Standort).where(Standort.deleted_at.is_(None))
    if name is not None:
        statement = statement.where(Standort.name.ilike(f"%{name}%"))
    if ort is not None:
        statement = statement.where(Standort.ort.ilike(f"%{ort}%"))
    return list(session.scalars(statement.order_by(Standort.name)).all())


def get(session: Session, standort_id: uuid.UUID) -> Standort:
    standort = session.scalar(
        select(Standort).where(Standort.id == standort_id, Standort.deleted_at.is_(None))
    )
    if standort is None:
        raise NotFoundError("Standort", standort_id)
    return standort


def ensure_exists(session: Session, standort_id: uuid.UUID) -> None:
    aktiv = session.scalar(
        select(Standort.id).where(Standort.id == standort_id, Standort.deleted_at.is_(None))
    )
    if aktiv is None:
        raise NotFoundError("Standort", standort_id)


def update(session: Session, standort_id: uuid.UUID, data: StandortUpdate) -> Standort:
    ensure_exists(session, standort_id)
    update_with_version(
        session,
        Standort,
        standort_id,
        data.version,
        {"name": data.name, "ort": data.ort},
    )
    session.commit()
    session.expire_all()
    return get(session, standort_id)


def soft_delete(session: Session, standort_id: uuid.UUID) -> None:
    ensure_exists(session, standort_id)
    timestamp = datetime.now(UTC)
    maschinen_ids = cascade.active_maschinen_ids(session, standort_id)
    cascade.soft_delete_kaffeebohnen(session, maschinen_ids, timestamp)
    cascade.soft_delete_maschinen(session, maschinen_ids, timestamp)
    session.execute(
        sql_update(Standort)
        .where(Standort.id == standort_id)
        .values(
            deleted_at=timestamp,
            version=Standort.version + 1,
            updated_at=func.now(),
        )
        .execution_options(synchronize_session=False)
    )
    session.commit()


def hard_delete(session: Session, standort_id: uuid.UUID) -> None:
    standort = get(session, standort_id)
    session.delete(standort)
    session.commit()
