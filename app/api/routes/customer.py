from fastapi import APIRouter, Path
import structlog

from app.models import (
    RelatedAppointmentPublic,
    Roles,
    AppointmentStatus,
    UpdateAppointmentStatus,
)
from app.api.debs import role_dependency, db_dependency
from app.crud import update_appointment_status

log = structlog.get_logger()

router = APIRouter(prefix="/customer", tags=["customer"])


@router.post(
    "/{appointment_id}/cancel-appointment", response_model=RelatedAppointmentPublic
)
async def customer_cancel_appointment(
    user: role_dependency[Roles.CUSTOMER],
    db: db_dependency,
    appointment_id: int = Path(ge=0),
):
    payload = UpdateAppointmentStatus(new_status=AppointmentStatus.CANCELLED)
    result = await update_appointment_status(
        payload, appointment_id, db, customer_id=user.id
    )
    return result
