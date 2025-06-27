from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.models.lesson_progress import LessonProgress
from app.models.base import Base
from app.models.file import File

# Association table for lesson files (images or videos)
lesson_files = Table(
    "lesson_files",
    Base.metadata,
    Column("lesson_id", Integer, ForeignKey("lesson.id", ondelete="CASCADE"), primary_key=True),
    Column("file_id", Integer, ForeignKey("file.id", ondelete="CASCADE"), primary_key=True)
)

class Lesson(Base):
    __tablename__ = 'lesson'
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey('module.id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    content = Column(Text)
    video = Column(String)
    order = Column(Integer, default=0)
    img_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    thumbnail_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    module = relationship('Module', back_populates='lessons')
    tests = relationship('LessonTest', back_populates='lesson', cascade='all, delete-orphan')
    progress = relationship('LessonProgress', back_populates='lesson', cascade='all, delete-orphan')
    files = relationship('File', secondary=lesson_files, lazy='selectin')
    image = relationship('File', foreign_keys=[img_id], lazy='selectin')
    thumbnail = relationship('File', foreign_keys=[thumbnail_id], lazy='selectin')
