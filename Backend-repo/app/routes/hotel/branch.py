from fastapi import APIRouter, Depends, status, HTTPException, Query, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import json
from typing import Optional

from ...core.dependencies import get_db_session, get_super_admin, get_current_active_user, get_client_ip, get_super_admin_or_admin
from ...models.core.user import User
from ...schemas.core.branch import HotelOnboardingResponse, HotelOnboardingUpdate, HotelOnboardingData
from ...schemas.hotel.branch import (
    BranchCreate, BranchCreateResponse, BranchResponse, BranchUpdate,
    BranchGetResponse, BranchListResponse, BranchList
)
from ...utils.exceptions import InsufficientPermissionsError, DataSegregationError
from ...services.hotel.branch import (
    create_branch as create_branch_service,
    get_hotel_for_onboarding as get_hotel_for_onboarding_service,
    update_hotel_onboarding as update_hotel_onboarding_service,
    get_branches_by_hotel,
    get_branch_by_sequence_and_creator,
    get_branch_by_id,
    update_branch as update_branch_service,
    delete_branch as delete_branch_service,
    OnboardingIncompleteError
)

# Router for internal-only branch management APIs
branch_management_router = APIRouter()
# Router for public-facing hotel onboarding APIs
public_onboarding_router = APIRouter()
# A separate router to catch incorrect old paths and provide a helpful error
legacy_path_router = APIRouter()

@branch_management_router.post("/branches", response_model=BranchCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    # All form fields
    name: str = Form(...),
    address_line_1: str = Form(None),
    address_line_2: str = Form(None),
    area: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    country: str = Form(None),
    pincode: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    owner_name: str = Form(None),
    gst_number: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    subscription_plan: str = Form(None),
    business_type: str = Form(None),
    description: str = Form(None),
    fssai_number: str = Form(None),
    tin_number: str = Form(None),
    professional_tax_reg_number: str = Form(None),
    trade_license_number: str = Form(None),
    defaultBranch: bool = Form(None),
    admin_name: str = Form(None),
    seating_capacity: int = Form(None),
    operating_hours: str = Form(None),
    bank_details: str = Form(None),
    social_media_links: str = Form(None),
    use_hotel_location: bool = Form(False),
    logo: UploadFile = File(None),
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
    client_ip: str = Depends(get_client_ip)
):
    """
    Create a new branch for the Super Admin's hotel.
    Only a Super Admin can perform this action.
    """
    try:
        import json
        _bank_details = json.loads(bank_details) if bank_details else None
        _social_media_links = json.loads(social_media_links) if social_media_links else None
        _operating_hours = json.loads(operating_hours) if operating_hours else None
        branch_data = BranchCreate(
            name=name,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            area=area,
            city=city,
            state=state,
            country=country,
            pincode=pincode,
            phone=phone,
            email=email,
            owner_name=owner_name,
            gst_number=gst_number,
            latitude=latitude,
            longitude=longitude,
            subscription_plan=subscription_plan,
            business_type=business_type,
            description=description,
            fssai_number=fssai_number,
            tin_number=tin_number,
            professional_tax_reg_number=professional_tax_reg_number,
            trade_license_number=trade_license_number,
            defaultBranch=defaultBranch,
            admin_name=admin_name,
            seating_capacity=seating_capacity,
            operating_hours=_operating_hours,
            bank_details=_bank_details,
            social_media_links=_social_media_links,
            use_hotel_location=use_hotel_location
        )
        new_branch = await create_branch_service(
            creator=current_user,
            branch_data=branch_data,
            db=db,
            client_ip=client_ip,
            logo=logo
        )

        return BranchCreateResponse(
            success=True,
            message=f"Branch '{new_branch.name}' created successfully.",
            # Use from_orm for robust and consistent serialization.
            # This avoids manual mapping and is less prone to lazy-loading errors.
            data=BranchResponse.from_orm(new_branch)
        )
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OnboardingIncompleteError as e:
        raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED, detail=str(e))
    except DataSegregationError as e:
        # This error means the super_admin has no hotel_id, which is a data integrity/setup issue.
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except IntegrityError:
        # This could happen if there's a unique constraint violation, though unlikely with our sequence logic.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A branch with similar details might already exist.")
    except Exception as e:
        # In a real app, you would log the exception `e` here
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the branch.")


@branch_management_router.get("/branches", response_model=BranchListResponse, status_code=status.HTTP_200_OK)
async def list_branches(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    List all active branches for the Super Admin's hotel with pagination.
    """
    try:
        branches, total = await get_branches_by_hotel(db, current_user, page, per_page)
        return BranchListResponse(
            success=True,
            data=BranchList(
                branches=[BranchResponse.from_orm(b) for b in branches],
                total=total,
                page=page,
                per_page=per_page
            )
        )
    except (InsufficientPermissionsError, DataSegregationError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@public_onboarding_router.get(
    "/onboarding",
    response_model=HotelOnboardingData,
    summary="Get Hotel Details for Onboarding"
)
async def get_hotel_onboarding_details(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_super_admin)
):
    """
    Retrieves the hotel's details for the onboarding form.
    """
    hotel = await get_hotel_for_onboarding_service(db, current_user.hotel_id, current_user)
    return hotel


@public_onboarding_router.put(
    "/onboarding",
    response_model=HotelOnboardingResponse,
    summary="Submit Hotel Onboarding Form"
)
async def update_hotel_onboarding_details(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_super_admin),
    client_ip: str = Depends(get_client_ip),
    # --- Explicit Form Fields for Clear Documentation ---
    name: Optional[str] = Form(None, description="Editable name of the hotel."),
    owner_name: Optional[str] = Form(None, description="Editable name of the hotel owner."),
    gst_number: Optional[str] = Form(None, description="Editable GST number of the hotel."),
    business_type: Optional[str] = Form(None, description="Type of business (e.g., Hotel, Restaurant)."),
    address_line_1: Optional[str] = Form(None, description="Primary address line."),
    address_line_2: Optional[str] = Form(None, description="Secondary address line."),
    area: Optional[str] = Form(None, description="Area or locality."),
    city: Optional[str] = Form(None, description="City of the hotel."),
    pincode: Optional[str] = Form(None, description="Pincode of the hotel."),
    state: Optional[str] = Form(None, description="State of the hotel."),
    country: Optional[str] = Form(None, description="Country of the hotel."),
    email: Optional[str] = Form(None, description="Contact email for the hotel."),
    phone: Optional[str] = Form(None, description="Contact phone number for the hotel."),
    latitude: Optional[float] = Form(None, description="Geographical latitude of the hotel."),
    longitude: Optional[float] = Form(None, description="Geographical longitude of the hotel."),
    description: Optional[str] = Form(None, description="A short description of the hotel."),
    fssai_number: Optional[str] = Form(None, description="FSSAI license number."),
    tin_number: Optional[str] = Form(None, description="TIN number."),
    professional_tax_reg_number: Optional[str] = Form(None, description="Professional Tax Registration Number."),
    trade_license_number: Optional[str] = Form(None, description="Trade License number."),
    bank_details: Optional[str] = Form(None, description="Bank account details as a JSON string."),
    social_media_links: Optional[str] = Form(None, description="Social media links as a JSON string."),
    # --- Explicit File Upload Field ---
    logo: Optional[UploadFile] = File(None, description="The hotel's logo image file (e.g., PNG, JPG).")
):
    """
    Submits the completed hotel onboarding form.
    """
    form_data = locals().copy()
    # Remove non-form data from the dictionary
    del form_data['db']
    del form_data['current_user']
    del form_data['client_ip']
    del form_data['logo']

    try:
        # Manually parse JSON string fields back into dictionaries
        if bank_details:
            form_data['bank_details'] = json.loads(bank_details)
        if social_media_links:
            form_data['social_media_links'] = json.loads(social_media_links)

        # Use the Pydantic model to validate and create the data dictionary
        onboarding_data_model = HotelOnboardingUpdate(**form_data)
        onboarding_data_dict = onboarding_data_model.model_dump(exclude_unset=True)

    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format for bank_details or social_media_links.")

    # The service now returns the fully formed response object, which we can return directly.
    onboarding_response = await update_hotel_onboarding_service(
        db=db, hotel_id=current_user.hotel_id, onboarding_data=onboarding_data_dict,
        logo=logo, current_user=current_user, client_ip=client_ip
    )
    return onboarding_response

@branch_management_router.get("/branches/{branch_sequence_id}", response_model=BranchGetResponse, status_code=status.HTTP_200_OK)
async def get_branch(
    branch_sequence_id: int,
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a single branch by its sequence ID.
    """
    try:
        branch = await get_branch_by_sequence_and_creator(db, branch_sequence_id, current_user)
        if not branch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found.")
        return BranchGetResponse(success=True, data=BranchResponse.from_orm(branch))
    except DataSegregationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@branch_management_router.get("/branch/{branch_id}", response_model=BranchGetResponse, status_code=status.HTTP_200_OK)
async def get_branch_id(
    branch_id: int,
    current_user: User = Depends(get_super_admin_or_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get a single branch by its sequence ID.
    """
    try:
        branch = await get_branch_by_id(db, branch_id)
        if not branch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found.")
        return BranchGetResponse(success=True, data=BranchResponse.from_orm(branch))
    except DataSegregationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")



@legacy_path_router.post("/branches")
async def legacy_create_branch_path():
    """
    This endpoint catches calls to the old, incorrect path and provides a helpful error.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="This endpoint has moved. Please use POST /api/v1/hotels/branches instead."
    )


@branch_management_router.put("/branches/{branch_id}", response_model=BranchGetResponse, status_code=status.HTTP_200_OK)
async def update_branch(
    branch_id: int,
    name: str = Form(None),
    address_line_1: str = Form(None),
    address_line_2: str = Form(None),
    area: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    country: str = Form(None),
    pincode: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    owner_name: str = Form(None),
    gst_number: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    subscription_plan: str = Form(None),
    business_type: str = Form(None),
    description: str = Form(None),
    fssai_number: str = Form(None),
    tin_number: str = Form(None),
    professional_tax_reg_number: str = Form(None),
    trade_license_number: str = Form(None),
    defaultBranch: bool = Form(None),
    admin_name: str = Form(None),
    seating_capacity: int = Form(None),
    operating_hours: str = Form(None),
    bank_details: str = Form(None),
    social_media_links: str = Form(None),
    logo: UploadFile = File(None),
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
    client_ip: str = Depends(get_client_ip)
):
    """
    Update an existing branch.
    """
    try:
        import json
        _bank_details = json.loads(bank_details) if bank_details else None
        _social_media_links = json.loads(social_media_links) if social_media_links else None
        _operating_hours = json.loads(operating_hours) if operating_hours else None
        update_data = BranchUpdate(
            name=name,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            area=area,
            city=city,
            state=state,
            country=country,
            pincode=pincode,
            phone=phone,
            email=email,
            owner_name=owner_name,
            gst_number=gst_number,
            latitude=latitude,
            longitude=longitude,
            subscription_plan=subscription_plan,
            business_type=business_type,
            description=description,
            fssai_number=fssai_number,
            tin_number=tin_number,
            professional_tax_reg_number=professional_tax_reg_number,
            trade_license_number=trade_license_number,
            defaultBranch=defaultBranch,
            admin_name=admin_name,
            seating_capacity=seating_capacity,
            operating_hours=_operating_hours,
            bank_details=_bank_details,
            social_media_links=_social_media_links
        )
        updated_branch = await update_branch_service(
            db=db,
            branch_id=branch_id,
            update_data=update_data,
            creator=current_user,
            client_ip=client_ip,
            logo=logo
        )
        return BranchGetResponse(success=True, data=BranchResponse.from_orm(updated_branch))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (InsufficientPermissionsError, DataSegregationError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@branch_management_router.delete("/branches/{branch_sequence_id}", status_code=status.HTTP_200_OK)
async def delete_branch(
    branch_sequence_id: int,
    current_user: User = Depends(get_super_admin),
    db: AsyncSession = Depends(get_db_session),
    client_ip: str = Depends(get_client_ip),
):
    """
    Delete a branch from the database.

    - If there are active users on the branch, the request is rejected with a validation error
      that includes the active user count.
    - If only inactive users exist on the branch, those users are deleted first and then
      the branch is hard-deleted.
    """
    try:
        await delete_branch_service(
            db=db,
            branch_sequence_id=branch_sequence_id,
            creator=current_user,
            client_ip=client_ip
        )
        return {"success": True, "message": "Branch deleted successfully."}
    except ValueError as e:
        # Validation / business rule failure (e.g. active users still attached)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except (InsufficientPermissionsError, DataSegregationError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")