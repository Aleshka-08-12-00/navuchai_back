from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.test import TestAccessEnum

class Lesson(Base):
    __tablename__ = 'lesson'
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey('module.id'), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    video = Column(String)
    order = Column(Integer, default=0)
    access = Column(Enum(TestAccessEnum, name='lesson_access_enum', create_type=False,
                        values_callable=lambda obj: [e.value for e in obj]),
                    nullable=False, default=TestAccessEnum.PRIVATE)
    module = relationship('Module', back_populates='lessons')
    tests = relationship('LessonTest', back_populates='lesson', cascade='all, delete-orphan')
    lesson_accesses = relationship('LessonAccess', back_populates='lesson', cascade='all, delete-orphan')
