from sqlalchemy import Column, Integer, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base


class FaqCategory(Base):
    __tablename__ = 'faq_categories'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    express = Column(Boolean, nullable=True, default=False)

    faqs = relationship('Faq', back_populates='category', cascade='all, delete-orphan')
    accesses = relationship('FaqCategoryAccess', back_populates='faq_category', cascade='all, delete-orphan')

    @property
    def user_group_ids(self) -> list[int]:
        return [access.user_group_id for access in self.accesses]
