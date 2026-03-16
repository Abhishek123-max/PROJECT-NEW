# HotelAgent API Documentation

## Authentication Endpoints

### 1. Login
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/login`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "username": "productafnan@rb.com",
  "password": "afnan123"
}
```

### 2. Login (Super Admin)
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/login`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "username": "afnan_sa@km1.com",
  "password": "superafnan"
}
```

### 3. Login (Admin)
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/login`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "afnan@admin.com",
  "password": "adminafnan"
}
```

### 4. Login (Manager)
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/login`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "affnan@manager.com",
  "password": "manageraffnan"
}
```

## User Creation Endpoints

### 1. Create Super Admin
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/users/super-admin`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "afnan@superadmin.com",
  "password": "superafnan",
  "hotel_name": "kabab magic",
  "owner_name": "Afnan",
  "hotel_location": "Jayanagar",
  "gst_number": "GST123456789"
}
```

### 2. Create Admin
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/users/admin`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "afnan@admin.com",
  "branch_id": 1,
  "password": "adminafnan"
}
```

### 3. Create Manager
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/users/manager`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "affnan@manager.com",
  "password": "manageraffnan",
  "branch_id": 1
}
```

### 4. Create Housekeeping
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/users/housekeeping`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "adarsh@housekeeping.com",
  "password": "housekeepingadarsh",
  "branch_id": 1
}
```

### 5. Create Cashier
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/users/cashier`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "afnan@cashier.com",
  "password": "cashierafnan",
  "branch_id": 1
}
```

### 6. Create Kitchen Staff
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/kitchen-staff`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "afnan@kitchen.com",
  "password": "kitchenafnan",
  "branch_id": 1
}
```

### 7. Create Waiters
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/waiters`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "afnan@waiter.com",
  "password": "waiterafnan",
  "branch_id": 1
}
```

### 8. Create Inventory Manager
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/inventory-manager`  
**Headers:** `Content-Type: application/json`  
**Payload:**
```json
{
  "email": "afnan@inventory.com",
  "password": "inventoryafnan",
  "branch_id": 1
}
```

## Notes
- All endpoints require `Content-Type: application/json` header
- Authentication endpoints return access_token and refresh_token
- User creation endpoints require appropriate permissions
- Branch_id is required for role-based user creation

## Unified User Management Endpoints

These endpoints provide a more modern and flexible way to manage users.

### 1. Create User (Unified)
**Request Type:** POST  
**Endpoint:** `http://localhost:8000/api/v1/auth/users/create`  
**Headers:** 
`Content-Type: application/json`
`Authorization: Bearer <your_token>` (e.g., product_admin token for creating super_admin)

**Payload (Example for Super Admin):**
```json
{
  "email": "superadmin@newhotel.com",
  "password": "securepassword123",
  "first_name": "Super",
  "last_name": "Admin",
  "phone": "+1234567890",
  "role_name": "super_admin",
  "hotel_name": "The New Hotel",
  "owner_name": "John Doe",
  "hotel_location": "New York"
}
```

**Payload (Example for Admin):**
```json
{
  "email": "admin@newhotel.com",
  "password": "securepassword123",
  "first_name": "Branch",
  "last_name": "Admin",
  "role_name": "admin",
  "branch_id": 1
}
```

### 2. Update User (Unified)
**Request Type:** PUT
**Endpoint:** `http://localhost:8000/api/v1/auth/users/update/{user_id}`
**Headers:** 
`Content-Type: application/json`
`Authorization: Bearer <your_token>`
**Payload:**
```json
{
  "first_name": "UpdatedFirstName",
  "is_active": false
}
```

### 3. Delete User (Unified)
**Request Type:** DELETE
**Endpoint:** `http://localhost:8000/api/v1/auth/users/{user_id}`
**Headers:** 
`Authorization: Bearer <your_token>`