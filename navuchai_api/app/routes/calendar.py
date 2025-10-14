from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.crud import (
    create_event, update_event, delete_event, get_event, list_events,
    add_attendee, update_attendee, remove_attendee, list_event_attendees,
    add_reminder, remove_reminder, get_user_calendar,
    authorized_required,
)
from app.schemas.calendar import (
    CalendarEventCreate, CalendarEventUpdate, CalendarEventOut,
    CalendarAttendeeCreate, CalendarAttendeeUpdate, CalendarAttendeeOut,
    CalendarReminderCreate, CalendarReminderOut, CalendarMyFilter,
)
from app.models import User
from typing import Any


router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


# Events endpoints
@router.post("/events", response_model=CalendarEventOut)
async def create_calendar_event(payload: CalendarEventCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    # Принудительно проставляем автора события текущим пользователем
    payload = CalendarEventCreate(**payload.dict(), created_by_user_id=current_user.id)
    event = await create_event(db, payload)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/events/{event_id}", response_model=CalendarEventOut)
async def get_calendar_event(event_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event


@router.get("/events", response_model=list[dict])
async def list_calendar_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required),
    organization_id: int | None = Query(default=None),
    from_dt: datetime | None = Query(default=None),
    to_dt: datetime | None = Query(default=None),
    types: list[str] | None = Query(default=None),
):
    events = await list_events(db, organization_id, from_dt, to_dt, types)
    def to_client(e) -> dict[str, Any]:
        return {
            "event_id": str(e.id),
            "title": e.title,
            "subtitle": e.subtitle,
            "start": e.starts_at,
            "end": e.ends_at,
            "color": e.color,
            "textColor": e.text_color,
            "data": {
                "type": e.type,
                "description": e.description,
                "link": e.link,
            },
        }
    return [to_client(e) for e in events]


@router.put("/events/{event_id}", response_model=CalendarEventOut)
async def update_calendar_event(event_id: int, payload: CalendarEventUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    event = await update_event(db, event_id, payload)
    await db.commit()
    await db.refresh(event)
    return event


@router.delete("/events/{event_id}")
async def delete_calendar_event(event_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    ok = await delete_event(db, event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    await db.commit()
    return {"status": "ok"}


# Attendees endpoints
@router.post("/events/{event_id}/attendees", response_model=CalendarAttendeeOut)
async def add_calendar_attendee(event_id: int, payload: CalendarAttendeeCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    attendee = await add_attendee(db, event_id, payload)
    await db.commit()
    await db.refresh(attendee)
    return attendee


@router.get("/events/{event_id}/attendees", response_model=list[CalendarAttendeeOut])
async def list_calendar_attendees(event_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    attendees = await list_event_attendees(db, event_id)
    return attendees


@router.put("/attendees/{attendee_id}", response_model=CalendarAttendeeOut)
async def update_calendar_attendee(attendee_id: int, payload: CalendarAttendeeUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    attendee = await update_attendee(db, attendee_id, payload)
    if not attendee:
        raise HTTPException(status_code=404, detail="Участник не найден")
    await db.commit()
    await db.refresh(attendee)
    return attendee


@router.delete("/attendees/{attendee_id}")
async def delete_calendar_attendee(attendee_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    ok = await remove_attendee(db, attendee_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Участник не найден")
    await db.commit()
    return {"status": "ok"}


# Reminders endpoints
@router.post("/events/{event_id}/reminders", response_model=CalendarReminderOut)
async def add_calendar_reminder(event_id: int, payload: CalendarReminderCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    reminder = await add_reminder(db, event_id, payload.minutes_before, payload.channel)
    await db.commit()
    await db.refresh(reminder)
    return reminder


@router.delete("/reminders/{reminder_id}")
async def delete_calendar_reminder(reminder_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(authorized_required)):
    ok = await remove_reminder(db, reminder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Напоминание не найдено")
    await db.commit()
    return {"status": "ok"}


# My calendar
from app.schemas.calendar import CalendarEventOut


@router.get("/my", response_model=list[dict])
async def get_my_calendar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required),
    from_dt: datetime | None = Query(default=None, alias='from'),
    to_dt: datetime | None = Query(default=None, alias='to'),
    types: list[str] | None = Query(default=None),
):
    filters = CalendarMyFilter(from_dt=from_dt, to_dt=to_dt, types=types)
    events = await get_user_calendar(db, current_user.id, filters)
    def to_client(e) -> dict[str, Any]:
        return {
            "event_id": str(e.id),
            "title": e.title,
            "subtitle": e.subtitle,
            "start": e.starts_at,
            "end": e.ends_at,
            "color": e.color,
            "textColor": e.text_color,
            "data": {
                "type": e.type,
                "description": e.description,
                "link": e.link,
            },
        }
    return [to_client(e) for e in events]

