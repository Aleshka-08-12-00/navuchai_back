from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


CalendarEventType = Literal['meeting','call','deadline','task','other']
CalendarAttendeeRole = Literal['organizer','participant','optional']
CalendarAttendeeStatus = Literal['invited','accepted','declined','tentative']


class CalendarEventBase(BaseModel):
    title: str = Field(max_length=255)
    subtitle: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    type: CalendarEventType = 'meeting'
    link: Optional[str] = None
    color: Optional[str] = Field(default=None, max_length=7)
    text_color: Optional[str] = Field(default=None, max_length=7)
    is_all_day: bool = False
    starts_at: datetime
    ends_at: datetime
    organization_id: Optional[int] = None


class CalendarEventCreate(CalendarEventBase):
    created_by_user_id: Optional[int] = None


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    subtitle: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    type: Optional[CalendarEventType] = None
    link: Optional[str] = None
    color: Optional[str] = Field(default=None, max_length=7)
    text_color: Optional[str] = Field(default=None, max_length=7)
    is_all_day: Optional[bool] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    organization_id: Optional[int] = None


class CalendarEventOut(CalendarEventBase):
    id: int
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CalendarAttendeeBase(BaseModel):
    user_id: int
    role: CalendarAttendeeRole = 'participant'
    status: CalendarAttendeeStatus = 'invited'
    reminder_minutes_before: Optional[int] = Field(default=None, ge=0)


class CalendarAttendeeCreate(CalendarAttendeeBase):
    pass


class CalendarAttendeeUpdate(BaseModel):
    role: Optional[CalendarAttendeeRole] = None
    status: Optional[CalendarAttendeeStatus] = None
    reminder_minutes_before: Optional[int] = Field(default=None, ge=0)


class CalendarAttendeeOut(CalendarAttendeeBase):
    id: int
    event_id: int
    notified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CalendarReminderBase(BaseModel):
    minutes_before: int = Field(ge=0)
    channel: str = 'system'


class CalendarReminderCreate(CalendarReminderBase):
    pass


class CalendarReminderOut(CalendarReminderBase):
    id: int
    event_id: int
    created_at: datetime
    updated_at: datetime


class CalendarMyFilter(BaseModel):
    from_dt: Optional[datetime] = Field(default=None, alias='from')
    to_dt: Optional[datetime] = Field(default=None, alias='to')
    types: Optional[list[CalendarEventType]] = None
