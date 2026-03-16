"""
Pydantic schemas for Table management.
"""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class TableStatus(str, Enum):
    available = "available"
    occupied = "occupied"
    reserved = "reserved"
    all = "all"


class TableCreate(BaseModel):
    table_number: str = Field(..., min_length=1, max_length=20)
    number_of_seats: int = Field(..., gt=0)
    status: TableStatus = Field(..., alias="initial_status")
    floor_id: int
    hall_id: Optional[int] = None
    section_id: Optional[int] = None
    assigned_to: Optional[List[int]] = None


class TableUpdate(BaseModel):
    table_number: Optional[str] = Field(None, min_length=1, max_length=20)
    number_of_seats: Optional[int] = Field(None, gt=0)
    status: Optional[TableStatus] = Field(None, alias="initial_status")
    assigned_to: Optional[List[int]] = None


class TableShift(BaseModel):
    floor_id: int
    hall_id: Optional[int] = None
    section_id: Optional[int] = None


class TableResponse(BaseModel):
    id: int
    table_number: str
    number_of_seats: int
    status: str
    table_sequence: int
    is_active: bool
    branch_id: int
    floor_id: int
    hall_id: Optional[int]
    section_id: Optional[int]
    # Table.assignees is a many-to-many relationship. The ORM model exposes a helper
    # property `assigned_to_ids` which returns a list of user IDs.
    #
    # We read from `assigned_to_ids` at validation-time (ORM -> schema) but serialize
    # the field as `assigned_to` in API responses.
    assigned_to: List[int] = Field(
        default_factory=list,
        validation_alias="assigned_to_ids",
        serialization_alias="assigned_to",
    )

    class Config:
        from_attributes = True

class TableCreateResponse(BaseModel):
    success: bool = True
    data: TableResponse

class TableList(BaseModel):
    """Container for a paginated list of tables."""
    tables: List[TableResponse]
    total: int = 0
    page: int = 1
    per_page: int = 10


class TableListApiResponse(BaseModel):
    success: bool = True
    data: TableList