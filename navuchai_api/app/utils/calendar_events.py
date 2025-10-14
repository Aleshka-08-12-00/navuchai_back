from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import CalendarEvent, CalendarEventAttendee, User


async def create_simple_event(
    db: AsyncSession,
    *,
    user_id: int,
    title: str,
    subtitle: Optional[str] = None,
    description: Optional[str] = None,
    type: str = 'task',
    starts_at: datetime,
    ends_at: Optional[datetime] = None,
    link: Optional[str] = None,
    created_by_user_id: Optional[int] = None,
    color: Optional[str] = None,
    text_color: Optional[str] = None,
    is_all_day: bool = False,
) -> CalendarEvent:
    # Определяем организацию из пользователя
    organization_id: Optional[int] = None
    try:
        u_q = await db.execute(select(User.organization_id).where(User.id == user_id))
        organization_id = u_q.scalar_one_or_none()
    except Exception:
        pass

    event = CalendarEvent(
        title=title,
        subtitle=subtitle,
        description=description,
        type=type,
        link=link,
        color=color,
        text_color=text_color,
        is_all_day=is_all_day,
        starts_at=starts_at,
        ends_at=ends_at or starts_at,
        created_by_user_id=created_by_user_id,
        organization_id=organization_id,
    )
    db.add(event)
    await db.flush()

    attendee = CalendarEventAttendee(
        event_id=event.id,
        user_id=user_id,
        role='participant',
        status='invited',
    )
    db.add(attendee)
    await db.commit()
    await db.refresh(event)
    return event


