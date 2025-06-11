from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class UserGroupMember(Base):
    __tablename__ = "user_group_member"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("user_group.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', name='unique_user_group'),
    )

    user = relationship("User", back_populates="group_memberships")
    group = relationship("UserGroup", back_populates="members") 