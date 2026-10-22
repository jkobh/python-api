import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

NAME_MAX_LENGTH = 100


class KaffeebohneCreate(BaseModel):
    sorte: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)


class KaffeebohneUpdate(BaseModel):
    sorte: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    version: int = Field(ge=0)


class KaffeebohneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sorte: str
    maschine_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    version: int


class MaschineCreate(BaseModel):
    modell: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)


class MaschineUpdate(BaseModel):
    modell: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    version: int = Field(ge=0)


class MaschineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    modell: str
    standort_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    version: int


class StandortCreate(BaseModel):
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    ort: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)


class StandortUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    ort: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    version: int = Field(ge=0)


class StandortRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    ort: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    version: int
    maschine: MaschineRead | None = None
