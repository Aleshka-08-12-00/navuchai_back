from sqlalchemy import Column, Integer, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class CategoryAccess(Base):
    __tablename__ = "category_access"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("category.id", ondelete="CASCADE"), nullable=False)
    user_group_id = Column(Integer, ForeignKey("user_group.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status_id = Column(Integer, ForeignKey("test_access_status.id"), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    category = relationship("Category", back_populates="category_accesses")
    user_group = relationship("UserGroup", back_populates="category_accesses")
    status = relationship("TestAccessStatus")


