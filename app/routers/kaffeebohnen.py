import uuid

from fastapi import APIRouter, Query, status

from app.dependencies import SessionDependency
from app.repositories import kaffeebohnen
from app.schemas import KaffeebohneCreate, KaffeebohneRead, KaffeebohneUpdate

router = APIRouter(prefix="/maschinen/{maschine_id}/kaffeebohnen", tags=["Kaffeebohnen"])


@router.post("", response_model=KaffeebohneRead, status_code=status.HTTP_201_CREATED)
def create_kaffeebohne(
    maschine_id: uuid.UUID, data: KaffeebohneCreate, session: SessionDependency
) -> KaffeebohneRead:
    return KaffeebohneRead.model_validate(kaffeebohnen.create(session, maschine_id, data))


@router.get("", response_model=list[KaffeebohneRead])
def list_kaffeebohnen(
    maschine_id: uuid.UUID,
    session: SessionDependency,
    sorte: str | None = Query(default=None, description="Teilstring-Suche in der Sorte"),
) -> list[KaffeebohneRead]:
    return [
        KaffeebohneRead.model_validate(item)
        for item in kaffeebohnen.list_by_maschine(session, maschine_id, sorte)
    ]


@router.get("/{kaffeebohne_id}", response_model=KaffeebohneRead)
def read_kaffeebohne(
    maschine_id: uuid.UUID, kaffeebohne_id: uuid.UUID, session: SessionDependency
) -> KaffeebohneRead:
    return KaffeebohneRead.model_validate(kaffeebohnen.get(session, maschine_id, kaffeebohne_id))


@router.put("/{kaffeebohne_id}", response_model=KaffeebohneRead)
def update_kaffeebohne(
    maschine_id: uuid.UUID,
    kaffeebohne_id: uuid.UUID,
    data: KaffeebohneUpdate,
    session: SessionDependency,
) -> KaffeebohneRead:
    return KaffeebohneRead.model_validate(
        kaffeebohnen.update(session, maschine_id, kaffeebohne_id, data)
    )


@router.delete("/{kaffeebohne_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kaffeebohne(
    maschine_id: uuid.UUID, kaffeebohne_id: uuid.UUID, session: SessionDependency
) -> None:
    kaffeebohnen.soft_delete(session, maschine_id, kaffeebohne_id)
