from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

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
import structlog

from app.core.db import Base
from app.core.security import get_password_hash

log = structlog.get_logger()


class Roles(Enum):
    USER = "user"
    CLEANER = "cleaner"
    ADMIN = "admin"
    MANAGER = "manager"
    CUSTOMER = "customer"


class AppointmentStatus(Enum):
    SUBMITTED = "submitted"
    COMPLETED = "completed"
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
    def password(self):  # pyright: ignore[reportRedeclaration]
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

    @hybrid_property
    def get_sum_of_collected_money_as_cleaner(self):
        if self.role is not Roles.CLEANER:
            raise AttributeError("You can't access this attribute")

        return sum([x.paid_amount_cents for x in self.appointments_as_cleaner])

    # @get_sum_of_collected_money_as_cleaner.expression
    # def get_sum_of_collected_money_as_cleaner(cls):
    #     return exists(Appointments.paid_amount_cents).where(Appointments.cleaner_id == cls.id)

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
    next_occurence_at: Mapped[datetime] = mapped_column(DateTime(True), nullable=True)
    parent_appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id"), nullable=True
    )
    address: Mapped[str]
    apartment_size: Mapped[ApartmentSize]
    paid_amount_cents: Mapped[int | None] = mapped_column(nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    cleaner: Mapped[User | None] = relationship(
        back_populates="appointments_as_cleaner",
        foreign_keys=[cleaner_id],
        lazy="selectin",
    )
    customer: Mapped[User] = relationship(
        back_populates="appointments_as_customer",
        foreign_keys=[customer_id],
        lazy="selectin",
    )
    parent_appointment: Mapped[Appointments | None] = relationship(
        back_populates="child_appointments",
        lazy="selectin",
        foreign_keys=[parent_appointment_id],
        remote_side=[id],
        join_depth=1,
    )
    child_appointments: Mapped[list[Appointments]] = relationship(
        back_populates="parent_appointment",
        lazy="selectin",
        foreign_keys=[parent_appointment_id],
        join_depth=1,
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
    hours: int = Field(gt=0)
    address: str = Field(min_length=6)
    apartment_size: ApartmentSize


class RelatedAppointmentPublic(BaseModel):
    id: int
    status: AppointmentStatus
    date: datetime
    hours: int
    is_recurred: bool
    next_occurence_at: datetime | None
    paid_amount_cents: int | None

    model_config = ConfigDict(from_attributes=True)


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
    paid_amount_cents: int | None
    createdAt: datetime
    updatedAt: datetime
    next_occurence_at: datetime | None

    parent_appointment: RelatedAppointmentPublic | None = None
    child_appointments: list[RelatedAppointmentPublic] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ChangeUserRole(BaseModel):
    target_role: Roles


class UpdateAppointmentStatus(BaseModel):
    new_status: AppointmentStatus


class AssignCleanerModel(BaseModel):
    cleaner_id: int


class CollectMoneyModel(BaseModel):
    paid_amount_cents: int = Field(ge=0)
    appointment_id: int


class CollectedMoneyResponse(BaseModel):
    sum_of_money: int


class CollectedMoneyCleanerAppointmentResponse(BaseModel):
    appointment_id: int = Field(validation_alias="id")
    cleaner_id: int
    paid_amount_cents: int
