import uuid

from fastapi import APIRouter, status

from app.dependencies import SessionDependency
from app.repositories import maschinen
from app.schemas import MaschineCreate, MaschineRead, MaschineUpdate

router = APIRouter(prefix="/standorte/{standort_id}/maschine", tags=["Maschinen"])


@router.post("", response_model=MaschineRead, status_code=status.HTTP_201_CREATED)
def create_maschine(
    standort_id: uuid.UUID, data: MaschineCreate, session: SessionDependency
) -> MaschineRead:
    return MaschineRead.model_validate(maschinen.create(session, standort_id, data))


@router.get("", response_model=MaschineRead)
def read_maschine(standort_id: uuid.UUID, session: SessionDependency) -> MaschineRead:
    return MaschineRead.model_validate(maschinen.get_by_standort(session, standort_id))


@router.put("", response_model=MaschineRead)
def update_maschine(
    standort_id: uuid.UUID, data: MaschineUpdate, session: SessionDependency
) -> MaschineRead:
    return MaschineRead.model_validate(maschinen.update_by_standort(session, standort_id, data))


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_maschine(standort_id: uuid.UUID, session: SessionDependency) -> None:
    maschinen.soft_delete_by_standort(session, standort_id)
