from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr


class BranchBase(BaseModel):
    """Base schema for branch data."""
    name: str = Field(..., min_length=2, max_length=100, description="Name of the branch")
    address_line_1: Optional[str] = Field(None, max_length=255, description="Primary address line.")
    address_line_2: Optional[str] = Field(None, max_length=255, description="Secondary address line.")
    area: Optional[str] = Field(None, max_length=100, description="Area or locality.")
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100, description="Country")
    pincode: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, description="Branch contact email")
    owner_name: Optional[str] = Field(None, max_length=100, description="Owner name")
    gst_number: Optional[str] = Field(None, max_length=20, description="GST number")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    subscription_plan: Optional[str] = Field(None, max_length=50, description="Subscription plan")
    business_type: Optional[str] = Field(None, max_length=100, description="Business type")
    # logo_url: Optional[str] = Field(None, max_length=255, description="Logo URL")
    description: Optional[str] = Field(None, description="Branch description")
    fssai_number: Optional[str] = Field(None, max_length=100, description="FSSAI number")
    tin_number: Optional[str] = Field(None, max_length=100, description="TIN number")
    professional_tax_reg_number: Optional[str] = Field(None, max_length=100, description="Professional tax registration number")
    trade_license_number: Optional[str] = Field(None, max_length=100, description="Trade license number")
    bank_details: Optional[Dict[str, Any]] = Field(None, description="Bank details for the branch")
    social_media_links: Optional[Dict[str, str]] = Field(None, description="Social media links for the branch")
    defaultBranch: Optional[bool] = Field(None, description="Indicates if this is the default branch")
    admin_name: Optional[str] = Field(None, max_length=100)
    seating_capacity: Optional[int] = Field(None, gt=0)
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours, e.g., {'mon': '9am-5pm'}")


class BranchCreate(BranchBase):
    """Schema for creating a new branch."""
    use_hotel_location: bool = Field(False, description="Use hotel's address for this branch")


class BranchUpdate(BaseModel):
    """Schema for updating an existing branch. All fields are optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Name of the branch")
    address_line_1: Optional[str] = Field(None, max_length=255, description="Primary address line.")
    address_line_2: Optional[str] = Field(None, max_length=255, description="Secondary address line.")
    area: Optional[str] = Field(None, max_length=100, description="Area or locality.")
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100, description="Country")
    pincode: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, description="Branch contact email")
    owner_name: Optional[str] = Field(None, max_length=100, description="Owner name")
    gst_number: Optional[str] = Field(None, max_length=20, description="GST number")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    subscription_plan: Optional[str] = Field(None, max_length=50, description="Subscription plan")
    business_type: Optional[str] = Field(None, max_length=100, description="Business type")
    # logo: Optional[str] = Field(None, max_length=255, description="Logo URL")
    description: Optional[str] = Field(None, description="Branch description")
    fssai_number: Optional[str] = Field(None, max_length=100, description="FSSAI number")
    tin_number: Optional[str] = Field(None, max_length=100, description="TIN number")
    professional_tax_reg_number: Optional[str] = Field(None, max_length=100, description="Professional tax registration number")
    trade_license_number: Optional[str] = Field(None, max_length=100, description="Trade license number")
    admin_name: Optional[str] = Field(None, max_length=100)
    defaultBranch: Optional[bool] = Field(None, description="Indicates if this is the default branch")
    seating_capacity: Optional[int] = Field(None, gt=0)
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours, e.g., {'mon': '9am-5pm'}")
    bank_details: Optional[Dict[str, Any]] = Field(None, description="Bank details for the branch")
    social_media_links: Optional[Dict[str, Any]] = Field(None, description="Social media links for the branch")


class BranchResponse(BranchBase):
    """Schema for the response when a branch is created or retrieved."""
    id: int = Field(..., description="Internal system ID of the branch")
    hotel_id: int = Field(..., description="ID of the hotel this branch belongs to")
    branch_sequence: int = Field(..., description="Hotel-specific sequence ID for the branch")
    defaultBranch: Optional[bool] = Field(None, description="Indicates if this is the default branch")

    class Config:
        from_attributes = True


class BranchCreateResponse(BaseModel):
    """Response wrapper for branch creation."""
    success: bool = True
    message: str
    data: BranchResponse


class BranchGetResponse(BaseModel):
    """Response wrapper for retrieving a single branch."""
    success: bool = True
    data: BranchResponse


class BranchList(BaseModel):
    """Container for a list of branches with pagination details."""
    branches: List[BranchResponse]
    total: int
    page: int
    per_page: int

class BranchListResponse(BaseModel):
    """Response wrapper for listing branches."""
    success: bool = True
    data: BranchList