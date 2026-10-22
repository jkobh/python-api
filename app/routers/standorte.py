import uuid

from fastapi import APIRouter, Query, status

from app.dependencies import SessionDependency
from app.repositories import standorte
from app.schemas import StandortCreate, StandortRead, StandortUpdate

router = APIRouter(prefix="/standorte", tags=["Standorte"])


@router.post("", response_model=StandortRead, status_code=status.HTTP_201_CREATED)
def create_standort(data: StandortCreate, session: SessionDependency) -> StandortRead:
    standort = standorte.create(session, data)
    return StandortRead.model_validate(standort)


@router.get("", response_model=list[StandortRead])
def list_standorte(
    session: SessionDependency,
    name: str | None = Query(default=None, description="Teilstring-Suche im Namen"),
    ort: str | None = Query(default=None, description="Teilstring-Suche im Ort"),
) -> list[StandortRead]:
    return [StandortRead.model_validate(item) for item in standorte.list_all(session, name, ort)]


@router.get("/{standort_id}", response_model=StandortRead)
def read_standort(standort_id: uuid.UUID, session: SessionDependency) -> StandortRead:
    return StandortRead.model_validate(standorte.get(session, standort_id))


@router.put("/{standort_id}", response_model=StandortRead)
def update_standort(
    standort_id: uuid.UUID, data: StandortUpdate, session: SessionDependency
) -> StandortRead:
    return StandortRead.model_validate(standorte.update(session, standort_id, data))


@router.delete("/{standort_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_standort(
    standort_id: uuid.UUID,
    session: SessionDependency,
    hard: bool = Query(default=False, description="Endgültig entfernen statt Soft-Delete"),
) -> None:
    if hard:
        standorte.hard_delete(session, standort_id)
        return
    standorte.soft_delete(session, standort_id)
