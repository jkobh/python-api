import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Entity(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid7)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    version: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )


class Standort(Entity):
    __tablename__ = "standorte"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    ort: Mapped[str] = mapped_column(String(100), nullable=False)

    maschine: Mapped[Maschine | None] = relationship(
        primaryjoin="and_(Standort.id == Maschine.standort_id, Maschine.deleted_at.is_(None))",
        foreign_keys="Maschine.standort_id",
        viewonly=True,
        uselist=False,
    )


class Maschine(Entity):
    __tablename__ = "maschinen"
    __table_args__ = (
        Index(
            "uq_maschinen_standort_aktiv",
            "standort_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    modell: Mapped[str] = mapped_column(String(100), nullable=False)
    standort_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("standorte.id", ondelete="CASCADE"), nullable=False
    )


class Kaffeebohne(Entity):
    __tablename__ = "kaffeebohnen"

    sorte: Mapped[str] = mapped_column(String(100), nullable=False)
    maschine_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("maschinen.id", ondelete="CASCADE"), nullable=False
    )
