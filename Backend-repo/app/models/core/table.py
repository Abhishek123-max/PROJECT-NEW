"""
SQLAlchemy model for the 'tables' table.
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, func,
    UniqueConstraint, CheckConstraint
)

from sqlalchemy.orm import relationship
from sqlalchemy import Table as SATable

from .auth import Base


table_assignees = SATable(
    "table_assignees",
    Base.metadata,
    Column("table_id", Integer, ForeignKey("tables.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)


class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)

    # Hierarchy Foreign Keys
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id", ondelete="CASCADE"), nullable=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=True, index=True)

    # Table Details
    table_number = Column(String(20), nullable=False)
    number_of_seats = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='available', index=True)
    table_sequence = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)


    # Audit Fields
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    branch = relationship("Branch")
    floor = relationship("Floor")
    hall = relationship("Hall")
    section = relationship("Section")
    assignees = relationship(
        "User",
        secondary=table_assignees,
        backref="assigned_tables"
    )
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    __table_args__ = (
        UniqueConstraint('branch_id', 'table_number', name='uq_branch_table_number'),
        CheckConstraint('NOT(section_id IS NOT NULL AND hall_id IS NULL)', name='chk_section_requires_hall'),
    )

    @property
    def assigned_to_ids(self):
        """Return assigned user IDs without triggering lazy loads when already populated."""
        if self.assignees is None:
            return []
        return [user.id for user in self.assignees]