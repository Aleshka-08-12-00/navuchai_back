from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class FaqCategoryAccess(Base):
    __tablename__ = "faq_category_access"

    id = Column(Integer, primary_key=True, index=True)
    faq_category_id = Column(Integer, ForeignKey("faq_categories.id", ondelete="CASCADE"), nullable=False)
    user_group_id = Column(Integer, ForeignKey("user_group.id", ondelete="CASCADE"), nullable=False)

    faq_category = relationship("FaqCategory", back_populates="accesses")
    user_group = relationship("UserGroup")
