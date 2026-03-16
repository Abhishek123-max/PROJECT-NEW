from typing import Optional, List
from pydantic import BaseModel, Field


class FloorBase(BaseModel):
    """Base schema for floor data."""
    floor_name: str = Field(..., min_length=2, max_length=100, description="Name of the floor, e.g., 'Lobby Level'")
    floor_number: int = Field(..., ge=0, description="Floor number (0 for Ground, 1 for First, etc.)")
    is_active: bool = Field(..., description="Indicates if the floor is active")

class FloorCreate(FloorBase):
    """Schema for creating a new floor."""
    floor_manager_ids: List[int] = Field(..., description="The IDs of the users assigned as floor managers.")


class FloorUpdate(BaseModel):
    """Schema for updating an existing floor. All fields are optional."""
    floor_name: Optional[str] = Field(None, min_length=2, max_length=100)
    floor_number: Optional[int] = Field(None, ge=0)
    floor_manager_ids: Optional[List[int]] = Field(None, description="The IDs of the new floor managers.")


class FloorResponse(FloorBase):
    """Schema for the response when a floor is created or retrieved."""
    id: int
    branch_id: int
    hotel_id: int
    floor_sequence: int
    floor_manager_ids: List[int]

    class Config:
        from_attributes = True



class FloorList(BaseModel):
    """Container for a list of floors."""
    floors: List[FloorResponse]
    total: int = 0
    page: int = 1
    per_page: int = 10


class FloorApiResponse(BaseModel):
    """Generic success response for floor APIs."""
    success: bool = True
    data: FloorResponse


class FloorListApiResponse(BaseModel):
    """Response for listing floors."""
    success: bool = True
    data: FloorList