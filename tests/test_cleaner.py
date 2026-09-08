from __future__ import annotations
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy import insert

from app.models import ApartmentSize, AppointmentStatus, Appointments
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import USERS

current_date = datetime.now(timezone.utc)





async def get_cleaner_tasks(client: AsyncClient, cleaner_headers):
    api = "/v1/cleaner/tasks"
    response = await client.get(api, headers=cleaner_headers)
    assert response.status_code == 200
    return response.json()


async def insert_appts(db_client: AsyncSession):
    APPOINTMENTS_INSTANCES = [
    {
        "cleaner_id": USERS["cleaner1"]["id"],
        "customer_id": USERS["customer1"]["id"],
        "status": AppointmentStatus.ASSIGNED,
        "date": current_date,
        "hours": 1,
        "is_recurred": False,
        "address": "cairo1",
        "apartment_size": ApartmentSize.LARGE,
        "next_occurence_at": current_date + timedelta(days=7),
    },
    {
        "cleaner_id": USERS["cleaner2"]["id"],
        "customer_id": USERS["customer1"]["id"],
        "status": AppointmentStatus.ASSIGNED,
        "date": current_date,
        "hours": 1,
        "is_recurred": False,
        "address": "cairo2",
        "apartment_size": ApartmentSize.LARGE,
        "next_occurence_at": current_date + timedelta(days=7),
    },
]
    appt_statement = insert(Appointments).returning(Appointments)
    appt_results = (
        (await db_client.execute(appt_statement, APPOINTMENTS_INSTANCES))
        .mappings()
        .all()
    )
    await db_client.commit()
    assert len(appt_results) >= 0

async def test_cleaner_tasks_appts(client: AsyncClient, db_client: AsyncSession, auth_headers_map):
    await insert_appts(db_client)
    cleaner1_tasks = await get_cleaner_tasks(client, auth_headers_map["cleaner1"])
    cleaner2_tasks = await get_cleaner_tasks(client, auth_headers_map["cleaner2"])
    assert cleaner1_tasks != cleaner2_tasks
