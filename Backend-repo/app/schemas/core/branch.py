"""Pydantic schemas for Branch management."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class BranchBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="The name of the branch.")

class BranchCreate(BranchBase):
    use_hotel_location: bool = True

    # Optional location fields, used if use_hotel_location is False
    address_line_1: Optional[str] = Field(None, description="The primary address line for the branch.")
    address_line_2: Optional[str] = Field(None, description="The secondary address line for the branch.")
    area: Optional[str] = Field(None, description="The area or locality of the branch.")
    city: Optional[str] = Field(None, description="The city where the branch is located.")
    state: Optional[str] = Field(None, description="The state where the branch is located.")
    pincode: Optional[str] = Field(None, max_length=10, description="The postal code for the branch location.")
    
    # Optional contact and operational fields
    phone: Optional[str] = Field(None, max_length=20, description="The contact phone number for the branch.")
    email: Optional[str] = Field(None, description="The contact email for the branch.")
    admin_name: Optional[str] = Field(None, max_length=100, description="The name of the branch manager.")
    seating_capacity: Optional[int] = Field(None, gt=0, description="The total seating capacity of the branch.")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="The operating hours of the branch.")
    code: Optional[str] = Field(None, max_length=20, description="A unique code for the branch.")

class BranchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None

class BranchOut(BaseModel):
    id: int
    hotel_id: int
    branch_sequence: int
    is_active: bool
    name: str
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    area: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int

    class Config:
        from_attributes = True


class BranchList(BaseModel):
    """Schema for a paginated list of branches."""
    branches: List[BranchOut]
    total: int
    page: int
    per_page: int


class BranchListResponse(BaseModel):
    """Response wrapper for a list of branches."""
    success: bool = True
    message: str = "Branches retrieved successfully"
    data: BranchList


class HotelOnboardingUpdate(BaseModel):
    """Schema for updating hotel details during onboarding."""
    name: Optional[str] = Field(None, description="Editable name of the hotel.")
    owner_name: Optional[str] = Field(None, description="Editable name of the hotel owner.")
    gst_number: Optional[str] = Field(None, description="Editable GST number of the hotel.")
    business_type: Optional[str] = Field(None, description="Type of business (e.g., Hotel, Restaurant).")
    address_line_1: Optional[str] = Field(None, description="Primary address line.")
    address_line_2: Optional[str] = Field(None, description="Secondary address line.")
    area: Optional[str] = Field(None, description="Area or locality.")
    city: Optional[str] = Field(None, description="City of the hotel.")
    pincode: Optional[str] = Field(None, description="Pincode of the hotel.")
    state: Optional[str] = Field(None, description="State of the hotel.")
    country: Optional[str] = Field(None, description="Country of the hotel.")
    email: Optional[str] = Field(None, description="Contact email for the hotel.")
    phone: Optional[str] = Field(None, description="Contact phone number for the hotel.")
    latitude: Optional[float] = Field(None, description="Geographical latitude of the hotel.")
    longitude: Optional[float] = Field(None, description="Geographical longitude of the hotel.")
    description: Optional[str] = Field(None, description="A short description of the hotel.")
    fssai_number: Optional[str] = Field(None, description="FSSAI license number.")
    tin_number: Optional[str] = Field(None, description="TIN number.")
    professional_tax_reg_number: Optional[str] = Field(None, description="Professional Tax Registration Number.")
    trade_license_number: Optional[str] = Field(None, description="Trade License number.")
    bank_details: Optional[Dict[str, Any]] = Field(None, description="Bank account details.")
    social_media_links: Optional[Dict[str, Any]] = Field(None, description="Links to social media profiles.")


class HotelOnboardingData(BaseModel):
    """Schema for the hotel's data returned after onboarding."""
    id: int
    name: str
    hotel_code: Optional[str] = None
    owner_name: Optional[str] = None
    gst_number: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    subscription_plan: Optional[str] = None
    is_active: bool
    onboarding_status: str
    business_type: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    fssai_number: Optional[str] = None
    tin_number: Optional[str] = None
    professional_tax_reg_number: Optional[str] = None
    trade_license_number: Optional[str] = None
    bank_details: Optional[Dict[str, Any]] = None
    social_media_links: Optional[Dict[str, Any]] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HotelOnboardingResponse(BaseModel):
    """Response schema for the hotel onboarding update endpoint."""
    success: bool
    data: HotelOnboardingData