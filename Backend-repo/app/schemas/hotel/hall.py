"""
Pydantic schemas for Hall management.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class HallBase(BaseModel):
    hall_name: str = Field(..., min_length=1, max_length=100, description="Name of the hall")
    #hall_type: Optional[str] = Field(None, max_length=50, description="Type of the hall (e.g., 'Dining', 'Banquet')")
    hall_capacity: Optional[int] = Field(None, description="Capacity of the hall")

class HallCreate(HallBase):
    pass


class HallUpdate(BaseModel):
    hall_name: Optional[str] = Field(None, min_length=1, max_length=100)
    hall_capacity: Optional[int] = Field(None, description="Capacity of the hall")

class HallStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Set hall active status (true or false)")


class HallResponse(HallBase):
    id: int
    hall_sequence: int
    floor_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class HallSuccessResponse(BaseModel):
    success: bool = True
    data: HallResponse


class HallList(BaseModel):
    """Container for a paginated list of halls."""
    halls: List[HallResponse]
    total: int = 0
    page: int = 1
    per_page: int = 10


class HallListApiResponse(BaseModel):
    success: bool = True
    data: HallList