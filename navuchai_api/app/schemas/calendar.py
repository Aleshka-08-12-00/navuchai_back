from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel


class CalendarEvent(BaseModel):
    id: str
    type: Literal[
        "test_access_start",
        "test_access_end",
        "test_group_start",
        "test_group_end",
        "course_enrolled",
        "adaptation_assigned",
        "adaptation_deadline",
        "adaptation_completed",
    ]
    title: str
    description: Optional[str] = None
    start: datetime
    end: Optional[datetime] = None
    meta: dict | None = None


class CalendarResponse(BaseModel):
    events: list[CalendarEvent]


class CalendarSimpleEvent(BaseModel):
    name: str
    start: datetime
    end: Optional[datetime] = None


class CalendarSimpleResponse(BaseModel):
    events: list[CalendarSimpleEvent]

