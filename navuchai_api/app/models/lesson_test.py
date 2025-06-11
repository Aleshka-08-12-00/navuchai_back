from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class LessonTest(Base):
    __tablename__ = 'lesson_test'
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey('lesson.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    required = Column(Boolean, default=True)
    lesson = relationship('Lesson', back_populates='tests')
    test = relationship('Test')
    __table_args__ = (UniqueConstraint('lesson_id', 'test_id', name='lesson_test_unique'),)
