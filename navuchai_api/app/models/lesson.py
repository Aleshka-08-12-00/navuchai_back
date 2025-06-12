from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Lesson(Base):
    __tablename__ = 'lesson'
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey('module.id'), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    video = Column(String)
    order = Column(Integer, default=0)
    module = relationship('Module', back_populates='lessons')
    tests = relationship('LessonTest', back_populates='lesson', cascade='all, delete-orphan')
