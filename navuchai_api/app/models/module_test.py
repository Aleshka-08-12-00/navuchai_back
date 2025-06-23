from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class ModuleTest(Base):
    __tablename__ = 'module_test'

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey('module.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    required = Column(Boolean, default=True)

    module = relationship('Module', back_populates='tests')
    test = relationship('Test')

    __table_args__ = (
        UniqueConstraint('module_id', 'test_id', name='module_test_unique'),
    )
