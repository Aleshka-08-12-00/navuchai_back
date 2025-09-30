from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class AdaptationElement(Base):
    __tablename__ = 'adaptation_element'

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey('adaptation_section.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(20), nullable=False)
    text_content = Column(Text, nullable=True)
    entity_type = Column(String(20), nullable=True)
    entity_id = Column(Integer, nullable=True)
    entity_title = Column(String(255), nullable=True)
    is_completed = Column(Boolean, nullable=False, server_default='false', default=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    completed_by = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    order_index = Column(Integer, nullable=False)
    parent_id = Column(Integer, ForeignKey('adaptation_element.id', ondelete='CASCADE'), nullable=True)
    level = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    section = relationship('AdaptationSection', back_populates='elements')
    parent = relationship('AdaptationElement', remote_side=[id])


