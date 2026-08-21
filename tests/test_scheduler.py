import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApartmentSize, AppointmentStatus, Appointments, Roles, User
from app.worker.scheduler import process_recurring_appointments

current_date = datetime.now(timezone.utc)
USERS = [
    {"id": 1, "name": "customer", "_hash_password": "customer", "role": Roles.CUSTOMER},
    {"id": 2, "name": "cleaner", "_hash_password": "cleaner", "role": Roles.CLEANER},
]
APPOINTMENT_ROW = {
    "cleaner_id": 2,
    "customer_id": 1,
    "status": AppointmentStatus.COMPLETED,
    "date": current_date,
    "hours": 1,
    "is_recurred": True,
    "address": "cairo",
    "apartment_size": ApartmentSize.LARGE,
    "paid_amount_cents": 4550,
    "next_occurence_at": current_date + timedelta(days=7),
}


async def test_db(db_client: AsyncSession):
    usr_statement = insert(User).returning(User)
    usr_results = (await db_client.scalars(usr_statement, USERS)).all()
    appt_statement = insert(Appointments).returning(Appointments)
    appt_results = await db_client.scalar(appt_statement, APPOINTMENT_ROW)
    assert appt_results is not None

    for _ in range(10):
            await process_recurring_appointments(db_client)

    appts_length = len((await db_client.scalars(select(Appointments))).all())
    assert appts_length == 2
