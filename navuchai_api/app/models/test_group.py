from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class TestGroup(Base):
    __tablename__ = 'test_group'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date_start = Column(TIMESTAMP(timezone=True), nullable=True)
    date_end = Column(TIMESTAMP(timezone=True), nullable=True)
    time_limit = Column(Integer, nullable=True)
    img_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    thumbnail_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    status_id = Column(Integer, ForeignKey('test_status.id', ondelete='RESTRICT'), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    img = relationship('File', foreign_keys=[img_id], lazy='selectin')
    thumbnail = relationship('File', foreign_keys=[thumbnail_id], lazy='selectin')
    status = relationship('TestStatus', foreign_keys=[status_id], lazy='selectin')
    tests = relationship('TestGroupTest', back_populates='test_group', cascade='all, delete-orphan')
    test_group_accesses = relationship('TestGroupAccess', back_populates='test_group', cascade='all, delete-orphan') 