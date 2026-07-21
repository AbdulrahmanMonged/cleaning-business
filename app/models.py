from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.security import get_password_hash


class AppointmentStatus(Enum):
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"


class User(AsyncAttrs, Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    _hash_password: Mapped[str]
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))

    appointments: Mapped[list["Appointments"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    role: Mapped["Roles"] = relationship(back_populates="user")

    @hybrid_property
    def password(self):
        pass

    @password.setter
    def password(self, value):
        self._hash_password = get_password_hash(value)


class Roles(AsyncAttrs, Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    user: Mapped[list["User"]] = relationship(back_populates="role")


class Appointments(AsyncAttrs, Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    cleaner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[AppointmentStatus] = mapped_column(
        default=AppointmentStatus.SUBMITTED
    )
    date: Mapped[datetime]
    hours: Mapped[int]
    is_recurred: Mapped[bool] = mapped_column(default=False)
    address: Mapped[str]
    apartment_size: Mapped[str]
    paid_amount: Mapped[float] = mapped_column(nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="appointments")

    @hybrid_property
    def suggested_cleaners(self):
        pass


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "v1"


class TokenPayload(BaseModel):
    sub: str | None = None
