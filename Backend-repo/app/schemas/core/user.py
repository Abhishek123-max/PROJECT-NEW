"""
User management schemas for HotelAgent API.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, root_validator
from fastapi import Form

from ...settings.constants import RoleNames


class SuperAdminCreate(BaseModel):
    """Super Admin creation schema."""
    first_name: str
    hotel_name: str
    owner_name: str
    hotel_location: str
    gst_number: str


class AdminCreate(BaseModel):
    """Admin creation schema."""
    first_name: str
    branch_id: Optional[int] = None


class ManagerCreate(BaseModel):
    """Manager creation schema."""
    first_name: str
    branch_id: int
    floor_id: Optional[int] = None
    section_id: Optional[int] = None


class StaffCreate(BaseModel):
    """Staff creation schema."""
    first_name: str
    branch_id: Optional[int] = None
    floor_id: Optional[int] = None
    section_id: Optional[int] = None

        
class UserCreate(BaseModel):
    """Generic user creation schema."""
    first_name: str


class UnifiedUserCreate(BaseModel):
    """Unified schema for creating users with different roles."""
    role_name: str
    # User details
    first_name: str
    last_name: Optional[str] = None
    phone: Optional[str] = None
    contact_email: EmailStr
    employee_pic: Optional[str] = None  # Stored path or URL after upload
    employee_id: Optional[str] = None
    # Fields for all roles
    branch_id: Optional[int] = None
    floor_id: Optional[int] = None
    section_id: Optional[int] = None
    # Additional fields for super_admin creation
    hotel_name: Optional[str] = None
    owner_name: Optional[str] = None
    hotel_location: Optional[str] = None
    gst_number: Optional[str] = None
    report_manager: Optional[str] = None
    date_of_birth: Optional[date] = None
    annual_salary: Optional[float] = None
    joining_date: Optional[date] = None
    department: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    country: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        role_name: str = Form(...),
        first_name: str = Form(...),
        last_name: Optional[str] = Form(None),
        phone: Optional[str] = Form(None),
        contact_email: EmailStr = Form(...),
        employee_id: Optional[str] = Form(None),
        branch_id: Optional[int] = Form(None),
        floor_id: Optional[int] = Form(None),
        section_id: Optional[int] = Form(None),
        hotel_name: Optional[str] = Form(None),
        owner_name: Optional[str] = Form(None),
        hotel_location: Optional[str] = Form(None),
        gst_number: Optional[str] = Form(None),
        report_manager: Optional[str] = Form(None),
        date_of_birth: Optional[date] = Form(None),
        annual_salary: Optional[float] = Form(None),
        joining_date: Optional[date] = Form(None),
        department: Optional[str] = Form(None),
        street_address: Optional[str] = Form(None),
        city: Optional[str] = Form(None),
        state: Optional[str] = Form(None),
        pin_code: Optional[str] = Form(None),
        country: Optional[str] = Form(None),
        emergency_contact_name: Optional[str] = Form(None),
        emergency_contact_phone: Optional[str] = Form(None),
        emergency_contact_relationship: Optional[str] = Form(None),
    ) -> "UnifiedUserCreate":
        """Helper to read form fields for multipart/form-data endpoints.

        Use in routes as: `user_data: UnifiedUserCreate = Depends(UnifiedUserCreate.as_form)`
        The file field (`employee_pic`) should be accepted separately as `UploadFile`.
        """
        return cls(
            role_name=role_name,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            contact_email=contact_email,
            employee_id=employee_id,
            branch_id=branch_id,
            floor_id=floor_id,
            section_id=section_id,
            hotel_name=hotel_name,
            owner_name=owner_name,
            hotel_location=hotel_location,
            gst_number=gst_number,
            report_manager=report_manager,
            date_of_birth=date_of_birth,
            annual_salary=annual_salary,
            joining_date=joining_date,
            department=department,
            street_address=street_address,
            city=city,
            state=state,
            pin_code=pin_code,
            country=country,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            emergency_contact_relationship=emergency_contact_relationship,
        )

class UserUpdate(BaseModel):
    """User update schema."""
    role_name: str
    # User details
    first_name: str
    last_name: Optional[str] = ""
    phone: Optional[str] = None
    contact_email: EmailStr
    employee_pic: Optional[str] = None  # Stored path or URL after upload
    employee_id: Optional[str] = None
    # Fields for all roles
    branch_id: Optional[int] = None
    floor_id: Optional[int] = None
    section_id: Optional[int] = None
    # Additional fields for super_admin creation
    hotel_name: Optional[str] = None
    owner_name: Optional[str] = None
    hotel_location: Optional[str] = None
    gst_number: Optional[str] = None
    report_manager: Optional[str] = None
    is_active: Optional[bool] = None
    feature_toggles: Optional[Dict[str, Any]] = None
    date_of_birth: Optional[date] = None
    annual_salary: Optional[float] = None
    joining_date: Optional[date] = None
    department: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    country: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        role_name: str = Form(...),
        first_name: str = Form(...),
        last_name: Optional[str] = Form(""),
        phone: Optional[str] = Form(None),
        contact_email: EmailStr = Form(...),
        employee_id: Optional[str] = Form(None),
        branch_id: Optional[int] = Form(None),
        floor_id: Optional[int] = Form(None),
        section_id: Optional[int] = Form(None),
        hotel_name: Optional[str] = Form(None),
        owner_name: Optional[str] = Form(None),
        hotel_location: Optional[str] = Form(None),
        gst_number: Optional[str] = Form(None),
        report_manager: Optional[str] = Form(None),
        is_active: Optional[bool] = Form(None),
        feature_toggles: Optional[str] = Form(None),
        date_of_birth: Optional[date] = Form(None),
        annual_salary: Optional[float] = Form(None),
        joining_date: Optional[date] = Form(None),
        department: Optional[str] = Form(None),
        street_address: Optional[str] = Form(None),
        city: Optional[str] = Form(None),
        state: Optional[str] = Form(None),
        pin_code: Optional[str] = Form(None),
        country: Optional[str] = Form(None),
        emergency_contact_name: Optional[str] = Form(None),
        emergency_contact_phone: Optional[str] = Form(None),
        emergency_contact_relationship: Optional[str] = Form(None),
    ) -> "UserUpdate":
        """
        Helper to read form fields for multipart/form-data endpoints.

        Use in routes as: `update_data: UserUpdate = Depends(UserUpdate.as_form)`
        The file field (`employee_pic`) should be accepted separately as `UploadFile`.
        """
        import json

        parsed_feature_toggles: Optional[Dict[str, Any]] = None
        if feature_toggles:
            try:
                parsed_feature_toggles = json.loads(feature_toggles)
            except Exception:
                parsed_feature_toggles = None

        return cls(
            role_name=role_name,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            contact_email=contact_email,
            employee_id=employee_id,
            branch_id=branch_id,
            floor_id=floor_id,
            section_id=section_id,
            hotel_name=hotel_name,
            owner_name=owner_name,
            hotel_location=hotel_location,
            gst_number=gst_number,
            report_manager=report_manager,
            is_active=is_active,
            feature_toggles=parsed_feature_toggles,
            date_of_birth=date_of_birth,
            annual_salary=annual_salary,
            joining_date=joining_date,
            department=department,
            street_address=street_address,
            city=city,
            state=state,
            pin_code=pin_code,
            country=country,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            emergency_contact_relationship=emergency_contact_relationship,
        )


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    username: str
    first_name: Optional[str] = None
    contact_email: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    role: Optional[str] = None
    hotel_id: Optional[int] = None
    branch_id: Optional[int] = None
    floor_id: Optional[int] = None
    section_id: Optional[int] = None
    report_manager: Optional[str] = None
    is_locked: Optional[bool] = None
    employee_id: Optional[str] = None
    employee_pic: Optional[str] = None
    is_active: bool
    feature_toggles: Dict[str, Any] = {}
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    date_of_birth: Optional[date] = None
    annual_salary: Optional[float] = None
    joining_date: Optional[date] = None
    department: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    country: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    class Config:
        from_attributes = True

        @root_validator(pre=True)
        def ensure_feature_toggles_dict(cls, values):
            ft = values.get('feature_toggles')
            if isinstance(ft, str):
                import json
                try:
                    values['feature_toggles'] = json.loads(ft)
                except Exception:
                    values['feature_toggles'] = {}
            elif ft is None:
                values['feature_toggles'] = {}
            return values


class UserCreateData(BaseModel):
    """Data part of the user creation response, including initial credentials for first-time setup."""
    username: str
    onetime_password: str
    reset_token: str
    id: int
    first_name: Optional[str] = None
    contact_email: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    hotel_id: Optional[int] = None
    branch_id: Optional[int] = None
    floor_id: Optional[int] = None
    section_id: Optional[int] = None
    report_manager: Optional[str] = None
    employee_id: Optional[str] = None
    is_active: bool
    feature_toggles: Dict[str, Any] = {}
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    date_of_birth: Optional[date] = None
    annual_salary: Optional[float] = None
    joining_date: Optional[date] = None
    department: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    country: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

    class Config:
        from_attributes = True

        @root_validator(pre=True)
        def ensure_feature_toggles_dict(cls, values):
            ft = values.get('feature_toggles')
            if isinstance(ft, str):
                import json
                try:
                    values['feature_toggles'] = json.loads(ft)
                except Exception:
                    values['feature_toggles'] = {}
            elif ft is None:
                values['feature_toggles'] = {}
            return values


class UserCreateResponse(BaseModel):
    """User creation response schema."""
    success: bool
    message: str
    data: UserCreateData


class SuperAdminCreateResponse(BaseModel):
    """Super Admin creation response schema."""
    success: bool
    message: str
    data: Dict[str, Any]


class UserUpdateResponse(BaseModel):
    """User update response schema."""
    success: bool
    message: str
    data: UserResponse


class UserLockStatusUpdate(BaseModel):
    """Request body for PATCH user lock status (is_locked)."""
    is_locked: bool


class UserDeleteResponse(BaseModel):
    """User delete response schema."""
    success: bool
    message: str


class UserList(BaseModel):
    """User list schema."""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int


class UserListResponse(BaseModel):
    """User list response schema."""
    success: bool
    message: str
    data: UserList