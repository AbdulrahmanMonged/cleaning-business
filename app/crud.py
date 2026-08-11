from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.security import verify_password
from app.models import (
    AppointmentCreateModel,
    AppointmentPublic,
    AppointmentStatus,
    Appointments,
    AssignCleanerModel,
    ChangeUserRole,
    Roles,
    UpdateAppointmentStatus,
    User,
    UserCreate,
    UserLogin,
    UserPublic,
)

RANDOM_HASH = "$argon2i$v=19$m=16,t=2,p=1$YXNkYXNkYXM$AVBfoT4P1h879+Muu0tCxQ"
log = structlog.get_logger()


async def create_user(user: UserCreate, db: AsyncSession):
    try:
        new_user = User(name=user.name, password=user.password)
        db.add(new_user)
        await db.flush()
        await db.refresh(new_user, ["role", "createdAt", "name"])
        return new_user
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )


async def login_user(form: UserLogin, db: AsyncSession):
    fetched_user = await db.scalar(select(User).where(User.name == form.username))
    if fetched_user is None:
        verify_password(form.password, RANDOM_HASH)
        return None
    result, updated_hash = verify_password(form.password, fetched_user._hash_password)
    if not result:
        return None
    if updated_hash is not None:
        fetched_user._hash_password = updated_hash
    return fetched_user


async def insert_appointment(
    appointment: AppointmentCreateModel,
    user: UserPublic,
    db: AsyncSession,
):
    new_model = Appointments(
        customer_id=user.id,
        date=appointment.date,
        hours=appointment.hours,
        address=appointment.address,
        apartment_size=appointment.apartment_size,
        child_appointments=[]
    )
    db.add(new_model)
    await db.flush()
    # log.info(instance=new_model.child_appointments)
    # await db.refresh(new_model, ["child_appointments"])
    return new_model


async def fetch_user_by_id(user_id: int, db: AsyncSession):
    fetched_user = await db.scalar(select(User).where(User.id == user_id))
    if fetched_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Could not find user"
        )
    # await db.refresh(
    #     fetched_user, ["appointments_as_cleaner", "appointments_as_customer"]
    # )
    return fetched_user


async def get_all_users_by_role(db: AsyncSession, role: Roles | None = None):
    statement = select(User)
    if role:
        statement = statement.where(User.role == role)
    scalar_results = await db.scalars(statement)
    results = scalar_results.all()


async def fetch_all_available_clenaers(db: AsyncSession):
    scalars_result = await db.scalars(
        select(User).where(User.is_available, User.role == Roles.CLEANER)
    )
    results = scalars_result.all()
    return results


async def change_role(
    user: UserPublic, target_user: ChangeUserRole, db: AsyncSession, user_id: int
):
    if user.role is not Roles.ADMIN:
        return None
    fetched_user = await fetch_user_by_id(user_id, db)
    fetched_user.role = target_user.target_role
    return fetched_user


async def fetch_all_appointments_by_status(
    db: AsyncSession, status: AppointmentStatus | None
):
    statement = select(Appointments)
    if status is not None:
        statement = statement.where(Appointments.status == status)
    scalars_results = await db.scalars(statement=statement)
    results = scalars_results.all()
    return results


async def fetch_appointment_by_id(appointment_id: int, db: AsyncSession):
    selected_appointment = await db.scalar(
        select(Appointments).where(Appointments.id == appointment_id)
    )
    if selected_appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find an appointment",
        )
    return selected_appointment


async def update_appointment_status(
    update_model: UpdateAppointmentStatus, appointment_id: int, db: AsyncSession
):
    selected_model = await fetch_appointment_by_id(appointment_id, db)
    if update_model.new_status == AppointmentStatus.CONFIRMED:
        selected_model.next_occurence_at = selected_model.date + timedelta(days=7)
    selected_model.status = update_model.new_status
    # await db.refresh(selected_model, ["customer", "cleaner"])
    return selected_model


async def assign_cleaner_to_appointment(
    appointment_id: int, payload: AssignCleanerModel, db: AsyncSession
):
    fetched_appointment = await fetch_appointment_by_id(appointment_id, db)
    cleaner = await fetch_user_by_id(payload.cleaner_id, db)
    if cleaner.role != Roles.CLEANER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="user is not a cleaner"
        )
    fetched_appointment.cleaner_id = payload.cleaner_id
    fetched_appointment.status = AppointmentStatus.ASSIGNED
    # await db.refresh(fetched_appointment, ["cleaner", "customer"])
    return fetched_appointment


async def trigger_is_recurred(appointment_id: int, db: AsyncSession):
    result = await db.scalar(
        update(Appointments)
        .where(Appointments.id == appointment_id)
        .values(is_recurred=True)
        .returning(Appointments)
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment does not exist"
        )
    # await db.refresh(result, attribute_names=["cleaner", "customer"])
    return result


async def get_cleaner_appointments(cleaner_id: int, db: AsyncSession):
    return (
        await db.scalars(
            select(Appointments).where(
                Appointments.cleaner_id == cleaner_id,
                or_(
                    Appointments.status == AppointmentStatus.SUBMITTED,
                    Appointments.status == AppointmentStatus.IN_PROGRESS,
                ),
            )
        )
    ).all()
