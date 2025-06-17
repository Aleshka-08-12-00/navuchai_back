from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.test import TestAccessEnum

class Module(Base):
    __tablename__ = 'module'
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    title = Column(String, nullable=False)
    order = Column(Integer, default=0)
    access = Column(Enum(TestAccessEnum, name='module_access_enum', create_type=False,
                        values_callable=lambda obj: [e.value for e in obj]),
                    nullable=False, default=TestAccessEnum.PRIVATE)
    course = relationship('Course', back_populates='modules')
    lessons = relationship('Lesson', back_populates='module', cascade='all, delete-orphan')
    module_accesses = relationship('ModuleAccess', back_populates='module', cascade='all, delete-orphan')
    tests = relationship('ModuleTest', back_populates='module', cascade='all, delete-orphan')
