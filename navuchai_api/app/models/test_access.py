from sqlalchemy import Column, Integer, DateTime, ForeignKey, TIMESTAMP, String, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class TestAccess(Base):
    """Модель доступа к тесту"""
    __tablename__ = "test_access"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("test.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("user_group.id", ondelete="CASCADE"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status_id = Column(Integer, ForeignKey("test_access_status.id"), nullable=False, default=1, server_default="1")
    completed_number = Column(Integer, nullable=True)
    avg_percent = Column(Integer, nullable=True)
    is_completed = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    access_code = Column(String, nullable=True, unique=True, index=True)

    test = relationship("Test", back_populates="test_accesses")
    user = relationship("User", back_populates="test_accesses")
    group = relationship("UserGroup", back_populates="test_accesses")
    status = relationship("TestAccessStatus", back_populates="test_accesses") 