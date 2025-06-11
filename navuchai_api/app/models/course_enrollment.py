from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base

class CourseEnrollment(Base):
    __tablename__ = 'course_enrollment'
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    enrolled_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    course = relationship('Course', back_populates='enrollments')
    user = relationship('User')
    __table_args__ = (UniqueConstraint('course_id', 'user_id', name='course_user_unique'),)
