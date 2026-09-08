from __future__ import annotations
from datetime import datetime, timedelta, timezone

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApartmentSize, AppointmentStatus, Appointments
from app.worker.scheduler import process_recurring_appointments
from tests.conftest import USERS

current_date = datetime.now(timezone.utc)

APPOINTMENT_ROW = {
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
    APPOINTMENT_ROW["cleaner_id"] = USERS["cleaner1"]["id"]
    APPOINTMENT_ROW["customer_id"] = USERS["customer1"]["id"]
    appt_statement = insert(Appointments).returning(Appointments)
    appt_results = await db_client.scalar(appt_statement, APPOINTMENT_ROW)
    assert appt_results is not None

    for _ in range(10):
            await process_recurring_appointments(db_client)

    appts_length = len((await db_client.scalars(select(Appointments))).all())
    assert appts_length == 2
