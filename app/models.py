from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
)
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
    name: Mapped[str] = mapped_column(unique=True)
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

    appointments_as_cleaner: Mapped[list["Appointments"]] = relationship(
        back_populates="cleaner",
        cascade="all, delete-orphan",
        foreign_keys="Appointments.cleaner_id",
    )
    appointments_as_customer: Mapped[list["Appointments"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        foreign_keys="Appointments.customer_id",
    )
    role: Mapped["Roles"] = relationship(back_populates="user")

    @hybrid_property
    def password(self):
        return None

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
    cleaner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
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

    cleaner: Mapped["User"] = relationship(
        back_populates="appointments_as_cleaner", foreign_keys=[cleaner_id]
    )
    customer: Mapped["User"] = relationship(
        back_populates="appointments_as_customer", foreign_keys=[customer_id]
    )

    @hybrid_property
    def suggested_cleaners(self):
        pass


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "v1"


class TokenPayload(BaseModel):
    sub: str | None = None


class UserCreate(BaseModel):
    name: str = Field(min_length=3)
    password: str = Field(min_length=5)
    confirm_password: str = Field(min_length=5)

    @field_validator("confirm_password")
    def validate_confirm_password(cls, value: str, info: ValidationInfo):
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Password Do not match")
        return value


class UserPublic(BaseModel):
    name: str
    createdAt: datetime
    role: str
    # appointments: list[Appointments] = []

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @field_validator("role", mode="before")
    def validate_role(cls, value):
        if isinstance(value, Roles):
            return value.name
        return value

    @field_serializer("createdAt")
    def serialize_createdat(self, value: datetime):
        if isinstance(value, datetime):
            return value.strftime("%m/%d/%Y, %H:%M:%S")
        return value


class UserLogin(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=5)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
