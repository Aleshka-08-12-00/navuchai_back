from sqlalchemy import Column, Integer, DateTime, ForeignKey, TIMESTAMP, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class ModuleAccess(Base):
    """Модель доступа к модулю"""
    __tablename__ = "module_access"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("module.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("user_group.id", ondelete="CASCADE"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status_id = Column(Integer, ForeignKey("test_status.id"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    access_code = Column(String, nullable=True, unique=True, index=True)

    module = relationship("Module", back_populates="module_accesses")
    user = relationship("User")
    group = relationship("UserGroup")
    status = relationship("TestStatus")
