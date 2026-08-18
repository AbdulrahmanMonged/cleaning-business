import asyncio
from datetime import datetime, timedelta, timezone
import signal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import structlog

from app.core.db import get_engine
from app.models import AppointmentStatus, Appointments

log = structlog.get_logger()


async def create_next_occurence(appt: Appointments):
    new_instance = Appointments(
        customer_id=appt.customer_id,
        cleaner_id=appt.cleaner_id,
        date=appt.date + timedelta(days=7),
        hours=appt.hours,
        is_recurred=appt.is_recurred,
        parent_appointment_id=appt.id,
        address=appt.address,
        apartment_size=appt.apartment_size,
    )
    return new_instance


async def process_recurring_appointments(session: AsyncSession):
    stmt = (
        select(Appointments)
        .where(Appointments.is_recurred.is_(True))
        .where(Appointments.next_occurence_at.is_not(None))
        .where(Appointments.status == AppointmentStatus.COMPLETED)
        .with_for_update(skip_locked=True)
        .limit(100)
    )
    due = (await session.scalars(stmt)).all()
    new_instances = []
    for appt in due:
        new_instance = await create_next_occurence(appt)
        appt.next_occurence_at += timedelta(days=7)
        new_instances.append(new_instance)
    session.add_all(new_instances)
    await session.commit()
    return len(due)


async def run_recurring_check():
    session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with session_factory() as session:
        try:
            count = await process_recurring_appointments(session)
            log.info("recurring_check.completed", processed=count)
        except Exception:
            log.exception("recurring_check.failed")


def build_scheduler():
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_recurring_check,
        trigger=IntervalTrigger(minutes=15),
        id="recurring_appointments_check",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
        next_run_time=datetime.now(timezone.utc),
    )
    return scheduler


async def main():
    schedulder = build_scheduler()
    schedulder.start()
    log.info("scheduler.started")
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()
    log.info("scheduler.shutting_down")
    schedulder.shutdown(True)


if __name__ == "__main__":
    asyncio.run(main())
