from sqlalchemy import Boolean, Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Branch(Base):
    __tablename__ = "branches"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    hotel_id = Column(String)
    defaultbranch = Column(Boolean, default=False, nullable=True)

    def __repr__(self):
        return f"<Branch(id='{self.id}', name='{self.name}')>"