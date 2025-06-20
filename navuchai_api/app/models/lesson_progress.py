from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class LessonProgress(Base):
    __tablename__ = 'lesson_progress'

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey('lesson.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    completed_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    lesson = relationship('Lesson', back_populates='progress')
    user = relationship('User')

    __table_args__ = (UniqueConstraint('lesson_id', 'user_id', name='lesson_user_unique'),)
