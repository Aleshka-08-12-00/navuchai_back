from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class AdaptationSection(Base):
    __tablename__ = 'adaptation_section'

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('adaptation_template.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    order_index = Column(Integer, nullable=False)
    is_completed = Column(Boolean, nullable=False, server_default='false', default=False)
    completion_percentage = Column(Integer, nullable=False, server_default='0')
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    template = relationship('AdaptationTemplate', back_populates='sections')
    elements = relationship(
        'AdaptationElement',
        back_populates='section',
        cascade='all, delete-orphan',
        order_by='AdaptationElement.order_index',
        lazy='selectin'
    )


