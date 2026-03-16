from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    city = Column(String)
    country = Column(String)
    pincode = Column(String)

    def __repr__(self):
        return f"<Hotel(id='{self.id}', name='{self.name}')>"