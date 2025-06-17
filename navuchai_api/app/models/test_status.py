from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import Base


class TestStatus(Base):
    """Модель статуса теста"""
    __tablename__ = "test_status"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    code = Column(String(50), nullable=False)
    name_ru = Column(String(50), nullable=False)
    color = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    tests = relationship("Test", back_populates="status")
