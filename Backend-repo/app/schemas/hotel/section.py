"""
Pydantic schemas for Section management.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class SectionCreate(BaseModel):
    section_name: str = Field(..., min_length=1, max_length=100)
    section_type: Optional[str] = Field(None, max_length=50)
    tables: List[int] = Field(default_factory=list, description="Table IDs to assign to this section")


class SectionUpdate(BaseModel):
    section_name: Optional[str] = Field(None, min_length=1, max_length=100)
    section_type: Optional[str] = Field(None, max_length=50)
    tables: Optional[List[int]] = Field(
        default=None,
        description="Table IDs to (re)assign to this section; if omitted, tables are unchanged",
    )


class SectionResponse(BaseModel):
    id: int
    section_sequence: int
    section_name: str
    section_type: Optional[str]
    hall_id: int
    is_active: bool

    class Config:
        from_attributes = True


class SectionList(BaseModel):
    """Container for a paginated list of sections."""
    sections: List[SectionResponse]
    total: int = 0
    page: int = 1
    per_page: int = 10


class SectionListApiResponse(BaseModel):
    success: bool = True
    data: SectionList

class SectionSuccessResponse(BaseModel):
    success: bool = True
    data: SectionResponse