import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update as sql_update
from sqlalchemy.orm import Session

from app.models import Kaffeebohne
from app.repositories import maschinen
from app.repositories.errors import NotFoundError
from app.repositories.versioning import update_with_version
from app.schemas import KaffeebohneCreate, KaffeebohneUpdate


def create(session: Session, maschine_id: uuid.UUID, data: KaffeebohneCreate) -> Kaffeebohne:
    maschinen.get(session, maschine_id)
    kaffeebohne = Kaffeebohne(sorte=data.sorte, maschine_id=maschine_id)
    session.add(kaffeebohne)
    session.commit()
    session.refresh(kaffeebohne)
    return kaffeebohne


def list_by_maschine(
    session: Session, maschine_id: uuid.UUID, sorte: str | None
) -> list[Kaffeebohne]:
    maschinen.get(session, maschine_id)
    statement: Select[Kaffeebohne] = select(Kaffeebohne).where(
        Kaffeebohne.maschine_id == maschine_id, Kaffeebohne.deleted_at.is_(None)
    )
    if sorte is not None:
        statement = statement.where(Kaffeebohne.sorte.ilike(f"%{sorte}%"))
    return list(session.scalars(statement.order_by(Kaffeebohne.sorte)).all())


def get(session: Session, maschine_id: uuid.UUID, kaffeebohne_id: uuid.UUID) -> Kaffeebohne:
    kaffeebohne = session.scalar(
        select(Kaffeebohne).where(
            Kaffeebohne.id == kaffeebohne_id,
            Kaffeebohne.maschine_id == maschine_id,
            Kaffeebohne.deleted_at.is_(None),
        )
    )
    if kaffeebohne is None:
        raise NotFoundError("Kaffeebohne", kaffeebohne_id)
    return kaffeebohne


def update(
    session: Session,
    maschine_id: uuid.UUID,
    kaffeebohne_id: uuid.UUID,
    data: KaffeebohneUpdate,
) -> Kaffeebohne:
    get(session, maschine_id, kaffeebohne_id)
    update_with_version(session, Kaffeebohne, kaffeebohne_id, data.version, {"sorte": data.sorte})
    session.commit()
    session.expire_all()
    return get(session, maschine_id, kaffeebohne_id)


def soft_delete(session: Session, maschine_id: uuid.UUID, kaffeebohne_id: uuid.UUID) -> None:
    get(session, maschine_id, kaffeebohne_id)
    session.execute(
        sql_update(Kaffeebohne)
        .where(Kaffeebohne.id == kaffeebohne_id)
        .values(
            deleted_at=datetime.now(UTC),
            version=Kaffeebohne.version + 1,
            updated_at=func.now(),
        )
        .execution_options(synchronize_session=False)
    )
    session.commit()
