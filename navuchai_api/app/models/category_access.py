from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class CategoryAccess(Base):
    __tablename__ = "category_access"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    granted_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    category = relationship("Category", back_populates="accesses")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("category_id", "user_id", name="category_user_unique"),
    )
