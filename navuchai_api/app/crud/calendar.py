from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models import CalendarEvent, CalendarEventAttendee, CalendarEventReminder
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarAttendeeCreate,
    CalendarAttendeeUpdate,
    CalendarMyFilter,
)


# Events
async def create_event(db: AsyncSession, payload: CalendarEventCreate) -> CalendarEvent:
    event = CalendarEvent(
        title=payload.title,
        subtitle=payload.subtitle,
        description=payload.description,
        type=payload.type,
        link=payload.link,
        color=payload.color,
        text_color=payload.text_color,
        is_all_day=payload.is_all_day,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        created_by_user_id=payload.created_by_user_id,
        organization_id=payload.organization_id,
    )
    db.add(event)
    await db.flush()
    return event


async def update_event(db: AsyncSession, event_id: int, payload: CalendarEventUpdate) -> Optional[CalendarEvent]:
    q = await db.execute(select(CalendarEvent).where(CalendarEvent.id == event_id))
    event = q.scalar_one_or_none()
    if not event:
        return None
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(event, field, value)
    event.updated_at = datetime.utcnow()
    await db.flush()
    return event


async def delete_event(db: AsyncSession, event_id: int) -> bool:
    q = await db.execute(select(CalendarEvent.id).where(CalendarEvent.id == event_id))
    if not q.scalar_one_or_none():
        return False
    await db.execute(delete(CalendarEvent).where(CalendarEvent.id == event_id))
    return True


async def get_event(db: AsyncSession, event_id: int) -> Optional[CalendarEvent]:
    q = await db.execute(
        select(CalendarEvent)
        .options(selectinload(CalendarEvent.attendees), selectinload(CalendarEvent.reminders))
        .where(CalendarEvent.id == event_id)
    )
    return q.scalar_one_or_none()


async def list_events(db: AsyncSession, org_id: Optional[int], from_dt: Optional[datetime], to_dt: Optional[datetime], types: Optional[list[str]]):
    stmt = select(CalendarEvent)
    conditions = []
    if org_id is not None:
        conditions.append(CalendarEvent.organization_id == org_id)
    if from_dt is not None:
        conditions.append(CalendarEvent.ends_at >= from_dt)
    if to_dt is not None:
        conditions.append(CalendarEvent.starts_at <= to_dt)
    if types:
        conditions.append(CalendarEvent.type.in_(types))
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(CalendarEvent.starts_at)
    q = await db.execute(stmt)
    return q.scalars().all()


# Attendees
async def add_attendee(db: AsyncSession, event_id: int, payload: CalendarAttendeeCreate) -> CalendarEventAttendee:
    attendee = CalendarEventAttendee(
        event_id=event_id,
        user_id=payload.user_id,
        role=payload.role,
        status=payload.status,
        reminder_minutes_before=payload.reminder_minutes_before,
    )
    db.add(attendee)
    await db.flush()
    return attendee


async def update_attendee(db: AsyncSession, attendee_id: int, payload: CalendarAttendeeUpdate) -> Optional[CalendarEventAttendee]:
    q = await db.execute(select(CalendarEventAttendee).where(CalendarEventAttendee.id == attendee_id))
    attendee = q.scalar_one_or_none()
    if not attendee:
        return None
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(attendee, field, value)
    attendee.updated_at = datetime.utcnow()
    await db.flush()
    return attendee


async def remove_attendee(db: AsyncSession, attendee_id: int) -> bool:
    q = await db.execute(select(CalendarEventAttendee.id).where(CalendarEventAttendee.id == attendee_id))
    if not q.scalar_one_or_none():
        return False
    await db.execute(delete(CalendarEventAttendee).where(CalendarEventAttendee.id == attendee_id))
    return True


async def list_event_attendees(db: AsyncSession, event_id: int):
    q = await db.execute(select(CalendarEventAttendee).where(CalendarEventAttendee.event_id == event_id))
    return q.scalars().all()


# Reminders
async def add_reminder(db: AsyncSession, event_id: int, minutes_before: int, channel: str = 'system') -> CalendarEventReminder:
    reminder = CalendarEventReminder(event_id=event_id, minutes_before=minutes_before, channel=channel)
    db.add(reminder)
    await db.flush()
    return reminder


async def remove_reminder(db: AsyncSession, reminder_id: int) -> bool:
    q = await db.execute(select(CalendarEventReminder.id).where(CalendarEventReminder.id == reminder_id))
    if not q.scalar_one_or_none():
        return False
    await db.execute(delete(CalendarEventReminder).where(CalendarEventReminder.id == reminder_id))
    return True


# My calendar (by user attendance or creator)
async def get_user_calendar(db: AsyncSession, user_id: int, filters: Optional[CalendarMyFilter] = None):
    stmt = select(CalendarEvent).outerjoin(CalendarEventAttendee, CalendarEventAttendee.event_id == CalendarEvent.id)
    stmt = stmt.where((CalendarEvent.created_by_user_id == user_id) | (CalendarEventAttendee.user_id == user_id))
    if filters:
        if filters.from_dt is not None:
            stmt = stmt.where(CalendarEvent.ends_at >= filters.from_dt)
        if filters.to_dt is not None:
            stmt = stmt.where(CalendarEvent.starts_at <= filters.to_dt)
        if filters.types:
            stmt = stmt.where(CalendarEvent.type.in_(filters.types))
    stmt = stmt.order_by(CalendarEvent.starts_at)
    q = await db.execute(stmt.distinct())
    return q.scalars().all()


