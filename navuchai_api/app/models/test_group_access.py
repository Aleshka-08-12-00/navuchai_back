from sqlalchemy import Column, Integer, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class TestGroupAccess(Base):
    """Модель доступа к группе тестов"""
    __tablename__ = "test_group_access"

    id = Column(Integer, primary_key=True, index=True)
    test_group_id = Column(Integer, ForeignKey("test_group.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    user_group_id = Column(Integer, ForeignKey("user_group.id", ondelete="CASCADE"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status_id = Column(Integer, ForeignKey("test_access_status.id"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    test_group = relationship("TestGroup", back_populates="test_group_accesses")
    user = relationship("User", back_populates="test_group_accesses")
    user_group = relationship("UserGroup", back_populates="test_group_accesses")
    status = relationship("TestAccessStatus", back_populates="test_group_accesses") 