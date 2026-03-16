# JWT-Based ID Assignment for User Creation

## Overview

This document describes the implementation of JWT-based ID assignment for user creation in the HotelAgent application. The implementation ensures that hierarchical IDs (hotel_id, branch_id, zone_id, etc.) are automatically assigned from the JWT token payload when creating new users, maintaining proper data segregation based on the creator's context.

## Recent Updates

### Phone Field Addition

The User model has been updated to include a phone field to support storing user phone numbers. This change includes:

1. Adding the `phone` column to the `users` table in the database
2. Creating a migration script to update existing databases
3. Ensuring the User model accepts the phone parameter during user creation

## Implementation Details

### 1. User Service

The `create_unified_user` function in `app/services/core/user.py` has been enhanced to automatically assign hierarchical IDs from the JWT token payload when creating new users. This ensures that users are created within the appropriate context of the creator's hierarchy.

```python
# Automatically assign hierarchical IDs from JWT token if not explicitly provided
assigned_hotel_id = creator_token_payload.hotel_id
assigned_branch_id = branch_id if branch_id is not None else creator_token_payload.branch_id
assigned_zone_id = zone_id if zone_id is not None else creator_token_payload.zone_id
assigned_floor_id = floor_id if floor_id is not None else creator_token_payload.floor_id
assigned_section_id = section_id if section_id is not None else creator_token_payload.section_id
```

### 2. User Routes

The user creation routes in `app/routes/auth/users.py` have been updated to properly pass the JWT token payload to the user creation functions. This ensures that the hierarchical IDs are available for automatic assignment.

- Super Admin creation: `/auth/users/super-admin`
- Admin creation: `/auth/users/admin`
- Manager creation: `/auth/users/manager`
- Staff creation: `/auth/users/cashier`, `/auth/users/kitchen-staff`, etc.

### 3. Data Segregation

The implementation maintains proper data segregation by ensuring that users can only be created within the creator's context. For example:

- A Super Admin can create Admins within their hotel
- An Admin can create Managers within their branch
- A Manager can create staff within their zone

### 4. Role-Based Access Control

The implementation respects the role-based access control rules defined in the application:

- Product Admins can create Super Admins
- Super Admins can create Admins
- Admins can create Managers
- Managers can create staff (Cashiers, Kitchen Staff, etc.)

## Testing

A test script has been created at `scripts/test_jwt_id_assignment.py` to verify the JWT-based ID assignment implementation. The script tests two scenarios:

1. Creating a user with explicit IDs (which should override the token payload)
2. Creating a user without explicit IDs (which should use the token payload)

## Usage

When creating a new user, the JWT token payload of the creator is automatically used to assign hierarchical IDs if they are not explicitly provided. This ensures that users are created within the appropriate context of the creator's hierarchy.

```python
# Example: Creating an Admin user
new_admin = await create_admin(
    creator=current_user,
    email="admin@example.com",
    db=db,
    branch_id=branch_id,  # Optional - if not provided, will use creator's branch_id from JWT
    password="password123",
    creator_token_payload=token_payload  # JWT token payload with hierarchical IDs
)
```

## Benefits

- **Automatic ID Assignment**: Hierarchical IDs are automatically assigned from the JWT token payload, reducing the need for manual assignment.
- **Data Segregation**: Users are created within the appropriate context of the creator's hierarchy, maintaining proper data segregation.
- **Simplified API**: The API is simplified by allowing optional hierarchical IDs, which are automatically assigned if not provided.
- **Consistent User Creation**: The implementation ensures consistent user creation across different roles and contexts.