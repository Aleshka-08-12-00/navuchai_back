from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, CheckConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


calendar_attendee_role_enum = (
    'organizer',
    'participant',
    'optional',
)

calendar_attendee_status_enum = (
    'invited',
    'accepted',
    'declined',
    'tentative',
)


class CalendarEventAttendee(Base):
    __tablename__ = 'calendar_event_attendee'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('calendar_event.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    role = Column(Enum(*calendar_attendee_role_enum, name='calendar_attendee_role'), nullable=False, default='participant')
    status = Column(Enum(*calendar_attendee_status_enum, name='calendar_attendee_status'), nullable=False, default='invited')
    reminder_minutes_before = Column(Integer, nullable=True)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('reminder_minutes_before IS NULL OR reminder_minutes_before >= 0', name='attendee_reminder_minutes_non_negative'),
        Index('ix_calendar_event_attendee_user', 'user_id'),
        Index('ix_calendar_event_attendee_event', 'event_id'),
        Index('ix_calendar_event_attendee_status', 'status'),
    )

    event = relationship('CalendarEvent', back_populates='attendees')


