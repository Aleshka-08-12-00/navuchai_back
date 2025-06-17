from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class CourseTest(Base):
    __tablename__ = 'course_test'
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    required = Column(Boolean, default=True)
    course = relationship('Course', back_populates='tests')
    test = relationship('Test')
    __table_args__ = (UniqueConstraint('course_id', 'test_id', name='course_test_unique'),)
