from sqlalchemy import Column, Integer, Boolean, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class AdaptationElementStatus(Base):
    __tablename__ = 'adaptation_element_status'

    id = Column(Integer, primary_key=True, index=True)
    employee_adaptation_id = Column(Integer, ForeignKey('employee_adaptation.id', ondelete='CASCADE'), nullable=False)
    element_id = Column(Integer, ForeignKey('adaptation_element.id', ondelete='CASCADE'), nullable=False)
    is_completed = Column(Boolean, nullable=False, server_default='false', default=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    completed_by = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('employee_adaptation_id', 'element_id', name='uq_element_status_employee_element'),
    )

    employee_adaptation = relationship('EmployeeAdaptation')
    element = relationship('AdaptationElement')


