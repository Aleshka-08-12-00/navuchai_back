from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class CalendarEventReminder(Base):
    __tablename__ = 'calendar_event_reminder'

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('calendar_event.id', ondelete='CASCADE'), nullable=False)
    minutes_before = Column(Integer, nullable=False)
    channel = Column(String(50), nullable=False, default='system')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('minutes_before >= 0', name='reminder_minutes_non_negative'),
        Index('ix_calendar_event_reminder_event', 'event_id'),
    )

    event = relationship('CalendarEvent', back_populates='reminders')


