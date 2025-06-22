from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base

class Module(Base):
    __tablename__ = 'module'
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    course = relationship('Course', back_populates='modules')
    lessons = relationship('Lesson', back_populates='module', cascade='all, delete-orphan')
    tests = relationship('ModuleTest', back_populates='module', cascade='all, delete-orphan')
