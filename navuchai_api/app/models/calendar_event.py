from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, CheckConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


calendar_event_type_enum = (
    'meeting',
    'call',
    'deadline',
    'task',
    'other',
)


class CalendarEvent(Base):
    __tablename__ = 'calendar_event'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    type = Column(Enum(*calendar_event_type_enum, name='calendar_event_type'), nullable=False, default='meeting')
    link = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    text_color = Column(String(7), nullable=True)
    is_all_day = Column(Boolean, nullable=False, default=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    organization_id = Column(Integer, ForeignKey('organization.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('ends_at > starts_at', name='calendar_event_time_check'),
        Index('ix_calendar_event_starts_ends', 'starts_at', 'ends_at'),
        Index('ix_calendar_event_type', 'type'),
        Index('ix_calendar_event_org', 'organization_id'),
    )

    attendees = relationship('CalendarEventAttendee', back_populates='event', cascade='all, delete-orphan')
    reminders = relationship('CalendarEventReminder', back_populates='event', cascade='all, delete-orphan')


