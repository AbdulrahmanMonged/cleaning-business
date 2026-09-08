from __future__ import annotations
from datetime import datetime, timezone
import random

from httpx import AsyncClient
import structlog

from app.models import ApartmentSize, AppointmentStatus

appointments = {}

MANAGER_API = "/v1/manager"
APPOINTMENTS_API = "/v1/appointments"
CLEANER_API = "/v1/cleaner"
CUSTOMER_API = "/v1/customer"
logger = structlog.get_logger()


def appointment_payload_generator():
    return {
        "date": str(datetime.now(timezone.utc)),
        "hours": random.randint(1, 12),
        "address": random.choice(["Alex", "Cairo", "Giza", "Suez"]),
        "apartment_size": random.choice(list(ApartmentSize)).value,
    }


async def get_available_cleaners(client: AsyncClient, manager_headers):
    api = MANAGER_API + "/available-cleaners"
    response = await client.get(api, headers=manager_headers)

    assert response.status_code == 200
    return response.json()


async def test_appointment_submission(client: AsyncClient, auth_headers_map):
    logger.warn(auth_headers_map)
    api = APPOINTMENTS_API
    customer1_submission = await client.post(
        api,
        headers=auth_headers_map["customer1"],
        json=appointment_payload_generator(),
    )
    assert customer1_submission.status_code == 201
    appointments["customer1"] = customer1_submission.json()

    customer2_submission = await client.post(
        api,
        headers=auth_headers_map["customer2"],
        json=appointment_payload_generator(),
    )
    assert customer2_submission.status_code == 201
    appointments["customer2"] = customer2_submission.json()
    assert all(
        appointments[item]["status"] == AppointmentStatus.SUBMITTED.value
        for item in appointments
    )


async def test_manager_assign_cleaner(client: AsyncClient, auth_headers_map):
    available_cleaners = await get_available_cleaners(
        client, auth_headers_map["manager"]
    )
    logger.warn(available_cleaners=available_cleaners)
    api = f"{MANAGER_API}/{appointments["customer1"]["id"]}/assign-cleaner"
    response = await client.post(
        api,
        headers=auth_headers_map["manager"],
        json={"cleaner_id": available_cleaners[0]["id"]},
    )
    assert response.status_code == 200
    response_body = response.json()
    assert response_body["cleaner"]
    assert response_body["status"] == AppointmentStatus.ASSIGNED.value
    appointments["customer1"] = response.json()


async def test_cleaner_start_appointment(client: AsyncClient, auth_headers_map):
    api = CLEANER_API + f"/{appointments["customer1"]["id"]}/start-appointment"
    response = await client.post(
        api, headers=auth_headers_map[appointments["customer1"]["cleaner"]["name"]]
    )

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["status"] == AppointmentStatus.IN_PROGRESS.value


async def test_wrong_cleaner_start_appointment(client: AsyncClient, auth_headers_map):
    api1 = CLEANER_API + f"/{appointments["customer1"]["id"]}/start-appointment"
    api2 = CLEANER_API + f"/{appointments["customer2"]["id"]}/start-appointment"
    response1 = await client.post(api1, headers=auth_headers_map["cleaner2"])
    response2 = await client.post(api2, headers=auth_headers_map["cleaner2"])

    assert response1.status_code == 403
    assert response2.status_code == 403

async def test_customer_cancel_appointment(client: AsyncClient, auth_headers_map):
    api = CUSTOMER_API + f"/{appointments['customer2']["id"]}/cancel-appointment"
    response= await client.post(api, headers=auth_headers_map['customer2'])

    assert response.status_code == 200

    response_body = response.json()
    assert response_body["status"] == AppointmentStatus.CANCELLED.value


async def test_wrong_customer_cancel_appointment(client: AsyncClient, auth_headers_map):
    api = CUSTOMER_API + f"/{appointments['customer2']["id"]}/cancel-appointment"
    response= await client.post(api, headers=auth_headers_map['customer1'])

    assert response.status_code == 403

async def test_customer_cancel_on_going_appointment(client: AsyncClient, auth_headers_map):
    api = CUSTOMER_API + f"/{appointments['customer1']["id"]}/cancel-appointment"
    response= await client.post(api, headers=auth_headers_map['customer1'])

    assert response.status_code == 403
