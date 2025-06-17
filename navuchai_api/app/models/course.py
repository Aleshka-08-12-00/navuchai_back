from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.test import TestAccessEnum

class Course(Base):
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    author_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    access = Column(Enum(TestAccessEnum, name='course_access_enum', create_type=False,
                        values_callable=lambda obj: [e.value for e in obj]),
                    nullable=False, default=TestAccessEnum.PRIVATE)
    author = relationship('User')
    modules = relationship('Module', back_populates='course', cascade='all, delete-orphan')
    enrollments = relationship('CourseEnrollment', back_populates='course', cascade='all, delete-orphan')
    course_accesses = relationship('CourseAccess', back_populates='course', cascade='all, delete-orphan')
    tests = relationship('CourseTest', back_populates='course', cascade='all, delete-orphan')
