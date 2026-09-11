from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
import random
import pytest_asyncio
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
import structlog

from app.models import ApartmentSize, AppointmentStatus, Appointments
from tests.conftest import (
    USERS,
    MANAGER_API,
)

current_date = datetime.now(timezone.utc)

logger = structlog.get_logger()
APPOINTMENTS_ROWS = [
    {
        "status": AppointmentStatus.IN_PROGRESS,
        "date": current_date,
        "hours": 1,
        "is_recurred": False,
        "address": "cairo",
        "apartment_size": ApartmentSize.LARGE,
        "next_occurence_at": current_date + timedelta(days=7),
    },
    {
        "status": AppointmentStatus.IN_PROGRESS,
        "date": current_date,
        "hours": 1,
        "is_recurred": False,
        "address": "cairo",
        "apartment_size": ApartmentSize.LARGE,
        "next_occurence_at": current_date + timedelta(days=7),
    },
    {
        "status": AppointmentStatus.ASSIGNED,
        "date": current_date,
        "hours": 1,
        "is_recurred": False,
        "address": "cairo",
        "apartment_size": ApartmentSize.LARGE,
        "next_occurence_at": current_date + timedelta(days=7),
    },
    {
            "status": AppointmentStatus.IN_PROGRESS,
            "date": current_date,
            "hours": 1,
            "is_recurred": False,
            "address": "cairo",
            "apartment_size": ApartmentSize.LARGE,
            "next_occurence_at": current_date + timedelta(days=7),
        },
]

@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def insert_appts(db_client: AsyncSession):
    APPOINTMENTS_ROWS[0]["cleaner_id"] = USERS["cleaner1"]["id"]
    APPOINTMENTS_ROWS[0]["customer_id"] = USERS["customer1"]["id"]
    APPOINTMENTS_ROWS[1]["cleaner_id"] = USERS["cleaner2"]["id"]
    APPOINTMENTS_ROWS[1]["customer_id"] = USERS["customer2"]["id"]
    APPOINTMENTS_ROWS[2]["cleaner_id"] = USERS["cleaner2"]["id"]
    APPOINTMENTS_ROWS[2]["customer_id"] = USERS["customer2"]["id"]
    APPOINTMENTS_ROWS[3]["cleaner_id"] = USERS["cleaner2"]["id"]
    APPOINTMENTS_ROWS[3]["customer_id"] = USERS["customer2"]["id"]
    appt_statement = insert(Appointments).returning(Appointments.id)
    appt_results = (await db_client.execute(appt_statement, APPOINTMENTS_ROWS)).all()
    logger.info(appt=appt_results)
    assert len(appt_results) >= 0
    for i in range(len(appt_results)):
        APPOINTMENTS_ROWS[i]["appointment_id"] = appt_results[i][0]
    logger.info(appt=appt_results)
    await db_client.commit()


async def test_collect_money_wrong_cleaner(
    client: AsyncClient, auth_headers_map, insert_appts
):
    random_paid_amount = random.randint(10000, 99999)
    response = await client.post(
        "/v1/cleaner/collect-money",
        headers=auth_headers_map["cleaner2"],
        json={
            "paid_amount_cents": random_paid_amount,
            "appointment_id": APPOINTMENTS_ROWS[0]["appointment_id"],
        },
    )
    assert response.status_code == 403


async def test_collect_money_right_cleaner_non_progress(
    client: AsyncClient, auth_headers_map, insert_appts
):
    random_paid_amount = random.randint(10000, 99999)
    response = await client.post(
        "/v1/cleaner/collect-money",
        headers=auth_headers_map["cleaner2"],
        json={
            "paid_amount_cents": random_paid_amount,
            "appointment_id": APPOINTMENTS_ROWS[2]["appointment_id"],
        },
    )
    assert response.status_code == 403


async def test_collect_money_cleaner(
    client: AsyncClient, auth_headers_map, insert_appts
):
    random_paid_amount = random.randint(10000, 99999)
    response = await client.post(
        "/v1/cleaner/collect-money",
        headers=auth_headers_map["cleaner1"],
        json={
            "paid_amount_cents": random_paid_amount,
            "appointment_id": APPOINTMENTS_ROWS[0]["appointment_id"],
        },
    )
    APPOINTMENTS_ROWS[0]["paid_amount_cents"] = random_paid_amount
    logger.info(appt_instance=APPOINTMENTS_ROWS[0])
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == AppointmentStatus.COMPLETED.value
    assert json_response["paid_amount_cents"] == random_paid_amount


async def test_verify_manager_collect_money(
    client: AsyncClient, auth_headers_map, insert_appts
):
    response = await client.get(
        f"/v1/manager/{APPOINTMENTS_ROWS[0]["cleaner_id"]}/get-cleaner-appointment-collected-money",
        headers=auth_headers_map["manager"],
    )

    assert response.status_code == 200
    resp_body = response.json()

    logger.info(
        json_resp=resp_body, row_paid_cents=APPOINTMENTS_ROWS[0]["paid_amount_cents"]
    )

    assert (
        sum(item["paid_amount"] for item in resp_body)
        == APPOINTMENTS_ROWS[0]["paid_amount_cents"] / 1000
    )


async def test_manager_collect_money(
    client: AsyncClient, auth_headers_map, insert_appts
):
    random_paid_amount = random.randint(10000, 99999)
    APPOINTMENTS_ROWS[1]["paid_amount_cents"] = random_paid_amount
    API = MANAGER_API + "/collect-money"
    response = await client.post(
        API,
        headers=auth_headers_map["manager"],
        json={
            "paid_amount_cents": random_paid_amount,
            "appointment_id": APPOINTMENTS_ROWS[1]["appointment_id"],
            "cleaner_id": APPOINTMENTS_ROWS[1]["cleaner_id"],
        },
    )
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["paid_amount_cents"] == random_paid_amount
    assert response_body["status"] == AppointmentStatus.COMPLETED.value


async def test_manager_collect_money_wrong_cleaner(
    client: AsyncClient, auth_headers_map, insert_appts
):
    API = MANAGER_API + "/collect-money"
    random_paid_amount = random.randint(10000, 99999)
    response = await client.post(
        API,
        headers=auth_headers_map["manager"],
        json={
            "paid_amount_cents": random_paid_amount,
            "appointment_id": APPOINTMENTS_ROWS[1]["appointment_id"],
            "cleaner_id": APPOINTMENTS_ROWS[0]["cleaner_id"],
        },
    )
    assert response.status_code == 403


async def test_manager_collect_money_non_progress(
    client: AsyncClient, auth_headers_map, insert_appts
):
    API = MANAGER_API + "/collect-money"
    random_paid_amount = random.randint(10000, 99999)
    response = await client.post(
        API,
        headers=auth_headers_map["manager"],
        json={
            "paid_amount_cents": random_paid_amount,
            "appointment_id": APPOINTMENTS_ROWS[2]["appointment_id"],
            "cleaner_id": APPOINTMENTS_ROWS[2]["cleaner_id"],
        },
    )
    assert response.status_code == 403


async def test_manager_collect_money_non_existent_appt(
    client: AsyncClient, auth_headers_map, insert_appts
):
    API = MANAGER_API + "/collect-money"
    random_paid_amount = random.randint(10000, 99999)
    response = await client.post(
        API,
        headers=auth_headers_map["manager"],
        json={
            "paid_amount_cents": random_paid_amount,
            "appointment_id": 21412,
            "cleaner_id": APPOINTMENTS_ROWS[0]["cleaner_id"],
        },
    )
    assert response.status_code == 404


async def test_two_concurrent_requests_same_appt(
    client: AsyncClient, auth_headers_map, insert_appts
):
    API = MANAGER_API + "/collect-money"
    random_paid_amount = random.randint(10000, 99999)
    responses = await asyncio.gather(
        *(
            client.post(
                API,
                headers=auth_headers_map["manager"],
                json={
                    "paid_amount_cents": random_paid_amount,
                    "appointment_id": APPOINTMENTS_ROWS[3]["appointment_id"],
                    "cleaner_id": APPOINTMENTS_ROWS[3]["cleaner_id"],
                },
            ),
            client.post(
                API,
                headers=auth_headers_map["manager"],
                json={
                    "paid_amount_cents": random_paid_amount,
                    "appointment_id": APPOINTMENTS_ROWS[3]["appointment_id"],
                    "cleaner_id": APPOINTMENTS_ROWS[3]["cleaner_id"],
                },
            ),
        )
    )
    status_codes = [fut.status_code for fut in responses]
    assert 404 in status_codes and 200 in status_codes
