from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class TestAccessStatus(Base):
    __tablename__ = 'test_access_status'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(50), nullable=False)
    color = Column(String(7), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Обратная связь с TestAccess
    test_accesses = relationship("TestAccess", back_populates="status") 