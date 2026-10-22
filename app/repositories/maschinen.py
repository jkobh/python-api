import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Maschine
from app.repositories import cascade, standorte
from app.repositories.errors import ConflictError, NotFoundError
from app.repositories.versioning import update_with_version
from app.schemas import MaschineCreate, MaschineUpdate


def create(session: Session, standort_id: uuid.UUID, data: MaschineCreate) -> Maschine:
    standorte.ensure_exists(session, standort_id)
    vorhanden = session.scalar(
        select(Maschine.id).where(
            Maschine.standort_id == standort_id, Maschine.deleted_at.is_(None)
        )
    )
    if vorhanden is not None:
        raise ConflictError("Für diesen Standort existiert bereits eine Maschine.")
    maschine = Maschine(modell=data.modell, standort_id=standort_id)
    session.add(maschine)
    session.commit()
    session.refresh(maschine)
    return maschine


def get_by_standort(session: Session, standort_id: uuid.UUID) -> Maschine:
    standorte.ensure_exists(session, standort_id)
    maschine = session.scalar(
        select(Maschine).where(Maschine.standort_id == standort_id, Maschine.deleted_at.is_(None))
    )
    if maschine is None:
        raise NotFoundError("Maschine am Standort", standort_id)
    return maschine


def get(session: Session, maschine_id: uuid.UUID) -> Maschine:
    maschine = session.scalar(
        select(Maschine).where(Maschine.id == maschine_id, Maschine.deleted_at.is_(None))
    )
    if maschine is None:
        raise NotFoundError("Maschine", maschine_id)
    return maschine


def update_by_standort(session: Session, standort_id: uuid.UUID, data: MaschineUpdate) -> Maschine:
    maschine = get_by_standort(session, standort_id)
    update_with_version(session, Maschine, maschine.id, data.version, {"modell": data.modell})
    session.commit()
    session.expire_all()
    return get_by_standort(session, standort_id)


def soft_delete_by_standort(session: Session, standort_id: uuid.UUID) -> None:
    maschine = get_by_standort(session, standort_id)
    timestamp = datetime.now(UTC)
    cascade.soft_delete_kaffeebohnen(session, [maschine.id], timestamp)
    cascade.soft_delete_maschinen(session, [maschine.id], timestamp)
    session.commit()
