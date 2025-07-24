from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class TestGroupTest(Base):
    __tablename__ = 'test_group_test'
    id = Column(Integer, primary_key=True)
    test_group_id = Column(Integer, ForeignKey('test_group.id', ondelete='CASCADE'), nullable=False)
    test_id = Column(Integer, ForeignKey('test.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    test_group = relationship('TestGroup', back_populates='tests')
    test = relationship('Test') 