from __future__ import annotations
from datetime import datetime, timedelta, timezone
import random
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
import structlog

from app.models import ApartmentSize, AppointmentStatus, Appointments
from tests.conftest import USERS

current_date = datetime.now(timezone.utc)

logger = structlog.get_logger()
APPOINTMENT_ROW = {
    "status": AppointmentStatus.IN_PROGRESS,
    "date": current_date,
    "hours": 1,
    "is_recurred": False,
    "address": "cairo",
    "apartment_size": ApartmentSize.LARGE,
    "next_occurence_at": current_date + timedelta(days=7),
}


async def insert_appts(db_client: AsyncSession):
    APPOINTMENT_ROW["cleaner_id"] = USERS["cleaner1"]["id"]
    APPOINTMENT_ROW["customer_id"] = USERS["customer1"]["id"]
    appt_statement = insert(Appointments).returning(Appointments)
    appt_results = await db_client.scalar(appt_statement, APPOINTMENT_ROW)
    assert appt_results is not None

    await db_client.refresh(appt_results)
    APPOINTMENT_ROW["appointment_id"] = appt_results.id
    logger.info(appt=appt_results)
    await db_client.commit()


async def test_collect_money_wrong_cleaner(
    client: AsyncClient, auth_headers_map, db_client: AsyncSession
):
    await insert_appts(db_client)
    random_paid_amount = random.randint(100000000, 999999999)
    response = await client.post(
        "/v1/cleaner/collect-money",
        headers=auth_headers_map["cleaner2"],
        json={
            "paid_amount_cents": random_paid_amount,
            "appointment_id": APPOINTMENT_ROW["appointment_id"],
        },
    )
    assert response.status_code == 403


async def test_collect_money_cleaner(client: AsyncClient, auth_headers_map):
    random_paid_amount = random.randint(10000, 99999)
    response = await client.post(
        "/v1/cleaner/collect-money",
        headers=auth_headers_map["cleaner1"],
        json={
            "paid_amount_cents": random_paid_amount,
            "appointment_id": APPOINTMENT_ROW["appointment_id"],
        },
    )
    APPOINTMENT_ROW["paid_amount_cents"] = random_paid_amount
    logger.info(appt_instance=APPOINTMENT_ROW)
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == AppointmentStatus.COMPLETED.value
    assert json_response["paid_amount_cents"] == random_paid_amount


async def test_verify_manager_collect_money(client: AsyncClient, auth_headers_map):
    response = await client.get(
        f"/v1/manager/{APPOINTMENT_ROW["cleaner_id"]}/get-cleaner-appointment-collected-money",
        headers=auth_headers_map["manager"],
    )

    assert response.status_code == 200
    resp_body = response.json()

    logger.info(json_resp=resp_body)

    assert all(
        item["paid_amount"] == APPOINTMENT_ROW["paid_amount_cents"] / 1000
        for item in resp_body
    )
