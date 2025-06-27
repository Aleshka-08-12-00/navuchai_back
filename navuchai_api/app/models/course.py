from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.file import File
from app.models.base import Base

class Course(Base):
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    author_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    img_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    thumbnail_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    author = relationship('User')
    modules = relationship('Module', back_populates='course', cascade='all, delete-orphan')
    enrollments = relationship('CourseEnrollment', back_populates='course', cascade='all, delete-orphan')
    tests = relationship('CourseTest', back_populates='course', cascade='all, delete-orphan')
    image = relationship('File', foreign_keys=[img_id], lazy='selectin')
    thumbnail = relationship('File', foreign_keys=[thumbnail_id], lazy='selectin')
