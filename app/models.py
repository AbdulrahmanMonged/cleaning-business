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
from sqlalchemy import DateTime, ForeignKey, and_, exists
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.security import get_password_hash


class Roles(Enum):
    USER = "user"
    CLEANER = "cleaner"
    ADMIN = "admin"
    MANAGER = "manager"
    CUSTOMER = "customer"


class AppointmentStatus(Enum):
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"


class ApartmentSize(Enum):
    LARGE = "large"
    SMALL = "small"
    MEDIUM = "medium"


class User(AsyncAttrs, Base):
    __tablename__ = "users"
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

    role: Mapped[Roles] = mapped_column(default=Roles.USER)

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

    @hybrid_property
    def password(self):
        return None

    @password.setter
    def password(self, value):
        self._hash_password = get_password_hash(value)

    @hybrid_property
    def is_available(self):
        if self.role is not Roles.CLEANER:
            raise AttributeError("You can't access this attribute")
        
        return not any(
            x.status in (AppointmentStatus.ASSIGNED, AppointmentStatus.IN_PROGRESS)
            for x in self.appointments_as_cleaner
        )

    @is_available.expression
    def is_available(cls):
        return ~exists().where(
            and_(
                Appointments.cleaner_id == cls.id,
                Appointments.status.in_(
                    [AppointmentStatus.ASSIGNED, AppointmentStatus.IN_PROGRESS]
                ),
            )
        )


class Appointments(AsyncAttrs, Base):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(primary_key=True)
    cleaner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[AppointmentStatus] = mapped_column(
        default=AppointmentStatus.SUBMITTED
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    hours: Mapped[int]
    is_recurred: Mapped[bool] = mapped_column(default=False)
    address: Mapped[str]
    apartment_size: Mapped[ApartmentSize]
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
    id: int
    name: str
    createdAt: datetime
    role: Roles
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

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


class AppointmentCreateModel(BaseModel):
    date: datetime
    hours: int
    address: str
    apartment_size: ApartmentSize


class AppointmentPublic(BaseModel):
    id: int
    cleaner: UserPublic | None
    customer: UserPublic | None
    status: AppointmentStatus
    date: datetime
    hours: int
    address: str
    apartment_size: ApartmentSize
    is_recurred: bool
    paid_amount: float | None
    createdAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


class ChangeUserRole(BaseModel):
    target_role: Roles


class UpdateAppointmentStatus(BaseModel):
    new_status: AppointmentStatus


class AssignCleanerModel(BaseModel):
    cleaner_id: int
