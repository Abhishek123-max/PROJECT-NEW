"""
Documentation generation module for HotelAgent backend validation system.
Generates setup.md, postman.md, and troubleshooting documentation.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import sys

from .requirements_manager import RequirementsManager


class DocumentationGenerator:
    """Generates comprehensive documentation for HotelAgent backend."""
    
    def __init__(self, project_root: str = None):
        """
        Initialize documentation generator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.requirements_manager = RequirementsManager(project_root)
        
    def generate_setup_docs(self) -> str:
        """
        Generate comprehensive setup.md documentation.
        
        Returns:
            Path to generated setup.md file
            
        Raises:
            Exception: If documentation generation fails
        """
        try:
            setup_content = self._create_setup_content()
            setup_path = self.project_root / "setup.md"
            
            with open(setup_path, 'w', encoding='utf-8') as f:
                f.write(setup_content)
            
            return str(setup_path)
            
        except Exception as e:
            raise Exception(f"Failed to generate setup documentation: {str(e)}")
    
    def generate_api_docs(self, base_url: str = "https://localhost:8000") -> str:
        """
        Generate comprehensive postman.md documentation.
        
        Args:
            base_url: Base URL for API endpoints
            
        Returns:
            Path to generated postman.md file
            
        Raises:
            Exception: If documentation generation fails
        """
        try:
            api_content = self._create_api_content(base_url)
            api_path = self.project_root / "postman.md"
            
            with open(api_path, 'w', encoding='utf-8') as f:
                f.write(api_content)
            
            return str(api_path)
            
        except Exception as e:
            raise Exception(f"Failed to generate API documentation: {str(e)}")
    
    def generate_troubleshooting_guide(self) -> str:
        """
        Generate troubleshooting.md documentation.
        
        Returns:
            Path to generated troubleshooting.md file
            
        Raises:
            Exception: If documentation generation fails
        """
        try:
            troubleshooting_content = self._create_troubleshooting_content()
            troubleshooting_path = self.project_root / "troubleshooting.md"
            
            with open(troubleshooting_path, 'w', encoding='utf-8') as f:
                f.write(troubleshooting_content)
            
            return str(troubleshooting_path)
            
        except Exception as e:
            raise Exception(f"Failed to generate troubleshooting guide: {str(e)}")
    
    def _create_setup_content(self) -> str:
        """
        Create setup.md content with PowerShell commands.
        
        Returns:
            Setup documentation content
        """
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        content = f"""# HotelAgent Backend Setup Guide

Generated on: {datetime.now().isoformat()}

## Prerequisites

- Python {python_version} or higher
- PostgreSQL 12+ or Supabase account
- Redis server
- Git

## Environment Setup

### 1. Clone Repository

```powershell
git clone <repository-url>
cd hotel_agent
```

### 2. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\\venv\\Scripts\\Activate.ps1

# If execution policy prevents activation, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 4. Environment Configuration

Create `.env` file in the project root:

```powershell
# Copy example environment file
Copy-Item .env.example .env

# Edit .env file with your configuration
notepad .env
```

Required environment variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/hotelagent
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Configuration
DEBUG=true
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS=["*"]

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
BRUTE_FORCE_MAX_ATTEMPTS=5
BRUTE_FORCE_LOCKOUT_DURATION=900

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 5. Database Setup

#### Option A: PostgreSQL (Local)

```powershell
# Install PostgreSQL (if not installed)
# Download from: https://www.postgresql.org/download/windows/

# Create database
psql -U postgres -c "CREATE DATABASE hotelagent;"

# Run migrations
alembic upgrade head
```

#### Option B: Supabase (Cloud)

```powershell
# Set up Supabase project at https://supabase.com
# Update DATABASE_URL and SUPABASE_* variables in .env

# Run migrations
alembic upgrade head
```

### 6. Redis Setup

#### Option A: Redis (Local)

```powershell
# Install Redis for Windows
# Download from: https://github.com/microsoftarchive/redis/releases

# Start Redis server
redis-server

# Test Redis connection
redis-cli ping
```

#### Option B: Redis Cloud

```powershell
# Sign up at https://redis.com/try-free/
# Update REDIS_URL in .env file
```

### 7. Database Seeding (Optional)

```powershell
# Seed database with initial data
python scripts/seed_db.py
```

## Running the Application

### Development Server

```powershell
# Activate virtual environment
.\\venv\\Scripts\\Activate.ps1

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Using Python directly
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```powershell
# Install production server
pip install gunicorn

# Start production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Verification

### Health Checks

```powershell
# Check application health
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET

# Check readiness
Invoke-RestMethod -Uri "http://localhost:8000/ready" -Method GET
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database Connection Test

```powershell
# Test database connection
python -c "from app.core.database import get_db; print('Database connection successful')"
```

### Redis Connection Test

```powershell
# Test Redis connection
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print(r.ping())"
```

## Development Tools

### Running Tests

```powershell
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Code Quality

```powershell
# Install development tools
pip install black flake8 mypy isort

# Format code
black app/

# Check code style
flake8 app/

# Type checking
mypy app/

# Sort imports
isort app/
```

### Database Migrations

```powershell
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check migration status
alembic current
```

## Deployment

### Docker Deployment

```powershell
# Build Docker image
docker build -t hotelagent-backend .

# Run with Docker Compose
docker-compose up -d
```

### Environment-Specific Configuration

Create environment-specific `.env` files:

- `.env.development`
- `.env.staging`
- `.env.production`

```powershell
# Load specific environment
$env:ENV_FILE = ".env.production"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Monitoring and Logging

### Log Files

```powershell
# View application logs
Get-Content -Path "logs/app.log" -Tail 50 -Wait

# View error logs
Get-Content -Path "logs/error.log" -Tail 50 -Wait
```

### Performance Monitoring

```powershell
# Monitor system resources
Get-Process -Name "python" | Select-Object CPU, WorkingSet, ProcessName

# Monitor database connections
# Check PostgreSQL: SELECT * FROM pg_stat_activity;
# Check Redis: redis-cli info clients
```

## Security Considerations

### SSL/TLS Configuration

```powershell
# Generate self-signed certificate for development
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Run with HTTPS
uvicorn app.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem --host 0.0.0.0 --port 8443
```

### Environment Security

```powershell
# Set secure file permissions for .env
icacls .env /inheritance:r /grant:r "%USERNAME%:F"

# Generate secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Backup and Recovery

### Database Backup

```powershell
# PostgreSQL backup
pg_dump -U postgres -h localhost -d hotelagent > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Restore from backup
psql -U postgres -h localhost -d hotelagent < backup_20250109_103000.sql
```

### Configuration Backup

```powershell
# Backup configuration files
$backupDir = "backups/config_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir
Copy-Item .env, alembic.ini, requirements.txt $backupDir
```

## Common Issues and Solutions

See `troubleshooting.md` for detailed troubleshooting guide.

## Support

- Documentation: See `postman.md` for API documentation
- Issues: Create issue in project repository
- Contact: [Your contact information]

---

*This setup guide was generated automatically by the HotelAgent validation system.*
"""
        
        return content
    
    def _create_api_content(self, base_url: str) -> str:
        """
        Create postman.md content with all API endpoints.
        
        Args:
            base_url: Base URL for API endpoints
            
        Returns:
            API documentation content
        """
        content = f"""# HotelAgent API Documentation for Postman

Generated on: {datetime.now().isoformat()}
Base URL: {base_url}

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### 1. Health Check Endpoints

#### 1.1 Health Check
- **Method**: GET
- **URL**: `{base_url}/health`
- **Headers**: None required
- **Body**: None
- **Expected Response**:
```json
{{
  "status": "healthy",
  "timestamp": "2025-01-09T10:30:00Z"
}}
```

#### 1.2 Readiness Check
- **Method**: GET
- **URL**: `{base_url}/ready`
- **Headers**: None required
- **Body**: None
- **Expected Response**:
```json
{{
  "status": "ready",
  "timestamp": "2025-01-09T10:30:00Z"
}}
```

---

### 2. Authentication Endpoints

#### 2.1 User Login
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/login`
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "admin@example.com",
  "password": "securepassword123"
}}
```
- **Expected Response**:
```json
{{
  "success": true,
  "message": "Login successful",
  "data": {{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }},
  "user": {{
    "id": 1,
    "email": "admin@example.com",
    "role": "admin",
    "hotel_id": 1,
    "branch_id": 1,
    "is_active": true
  }}
}}
```

#### 2.2 Refresh Token
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/refresh`
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}}
```
- **Expected Response**:
```json
{{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}}
```

#### 2.3 User Logout
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/logout`
- **Headers**:
  ```
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```
- **Body**: None
- **Expected Response**:
```json
{{
  "success": true,
  "message": "Logout successful"
}}
```

#### 2.4 Get Current User Info
- **Method**: GET
- **URL**: `{base_url}/api/v1/auth/me`
- **Headers**:
  ```
  Authorization: Bearer <access_token>
  ```
- **Body**: None
- **Expected Response**:
```json
{{
  "success": true,
  "message": "User information retrieved successfully",
  "data": {{
    "id": 1,
    "email": "admin@example.com",
    "role": "admin",
    "hotel_id": 1,
    "branch_id": 1,
    "zone_id": null,
    "is_active": true,
    "feature_toggles": {{}},
    "last_login": "2025-01-09T10:30:00Z",
    "created_at": "2025-01-01T00:00:00Z"
  }}
}}
```

---

### 3. User Management Endpoints

#### 3.1 Create Super Admin
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/users/super-admin`
- **Headers**:
  ```
  Authorization: Bearer <product_admin_token>
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "superadmin@hotel.com",
  "password": "securepassword123",
  "hotel_name": "Grand Hotel",
  "owner_name": "John Doe",
  "hotel_location": "New York, NY",
  "gst_number": "GST123456789"
}}
```
- **Expected Response**:
```json
{{
  "success": true,
  "message": "Super Admin created successfully",
  "data": {{
    "user": {{
      "id": 2,
      "email": "superadmin@hotel.com",
      "role": "super_admin",
      "hotel_id": 1,
      "branch_id": 1,
      "is_active": true,
      "created_at": "2025-01-09T10:30:00Z"
    }},
    "hotel": {{
      "id": 1,
      "name": "Grand Hotel",
      "owner_name": "John Doe",
      "location": "New York, NY",
      "gst_number": "GST123456789"
    }},
    "branch": {{
      "id": 1,
      "name": "Main Branch",
      "location": "New York, NY"
    }}
  }}
}}
```

#### 3.2 Create Admin
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/users/admin`
- **Headers**:
  ```
  Authorization: Bearer <super_admin_token>
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "admin@hotel.com",
  "password": "securepassword123",
  "branch_id": 1
}}
```
- **Expected Response**:
```json
{{
  "success": true,
  "message": "Admin user created successfully",
  "data": {{
    "id": 3,
    "email": "admin@hotel.com",
    "role": "admin",
    "hotel_id": 1,
    "branch_id": 1,
    "is_active": true,
    "created_at": "2025-01-09T10:30:00Z"
  }}
}}
```

#### 3.3 Create Manager
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/users/manager`
- **Headers**:
  ```
  Authorization: Bearer <super_admin_or_admin_token>
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "manager@hotel.com",
  "password": "securepassword123",
  "zone_id": 1
}}
```
- **Expected Response**:
```json
{{
  "success": true,
  "message": "Manager user created successfully",
  "data": {{
    "id": 4,
    "email": "manager@hotel.com",
    "role": "manager",
    "hotel_id": 1,
    "branch_id": 1,
    "zone_id": 1,
    "is_active": true,
    "created_at": "2025-01-09T10:30:00Z"
  }}
}}
```

#### 3.4 Create Cashier
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/users/cashier`
- **Headers**:
  ```
  Authorization: Bearer <admin_or_manager_token>
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "cashier@hotel.com",
  "password": "securepassword123",
  "branch_id": 1,
  "zone_id": 1
}}
```
- **Expected Response**:
```json
{{
  "success": true,
  "message": "Cashier user created successfully",
  "data": {{
    "id": 5,
    "email": "cashier@hotel.com",
    "role": "cashier",
    "hotel_id": 1,
    "branch_id": 1,
    "zone_id": 1,
    "is_active": true,
    "created_at": "2025-01-09T10:30:00Z"
  }}
}}
```

#### 3.5 Create Kitchen Staff
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/users/kitchen-staff`
- **Headers**:
  ```
  Authorization: Bearer <admin_or_manager_token>
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "kitchen@hotel.com",
  "password": "securepassword123",
  "branch_id": 1,
  "zone_id": 1
}}
```

#### 3.6 Create Waiters
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/users/waiters`
- **Headers**:
  ```
  Authorization: Bearer <admin_or_manager_token>
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "waiter@hotel.com",
  "password": "securepassword123",
  "branch_id": 1,
  "zone_id": 1
}}
```

#### 3.7 Create Inventory Manager
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/users/inventory-manager`
- **Headers**:
  ```
  Authorization: Bearer <admin_or_manager_token>
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "inventory@hotel.com",
  "password": "securepassword123",
  "branch_id": 1,
  "zone_id": 1
}}
```

#### 3.8 Create Housekeeping
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/users/housekeeping`
- **Headers**:
  ```
  Authorization: Bearer <admin_or_manager_token>
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "housekeeping@hotel.com",
  "password": "securepassword123",
  "branch_id": 1,
  "zone_id": 1
}}
```

#### 3.9 Get User by ID
- **Method**: GET
- **URL**: `{base_url}/api/v1/auth/users/{{user_id}}`
- **Headers**:
  ```
  Authorization: Bearer <access_token>
  ```
- **Body**: None
- **Expected Response**:
```json
{{
  "success": true,
  "message": "User retrieved successfully",
  "data": {{
    "id": 1,
    "email": "user@hotel.com",
    "role": "admin",
    "hotel_id": 1,
    "branch_id": 1,
    "is_active": true,
    "created_at": "2025-01-09T10:30:00Z"
  }}
}}
```

#### 3.10 Update User
- **Method**: PUT
- **URL**: `{base_url}/api/v1/auth/users/{{user_id}}`
- **Headers**:
  ```
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "email": "newemail@hotel.com",
  "is_active": true
}}
```

#### 3.11 Delete User (Deactivate)
- **Method**: DELETE
- **URL**: `{base_url}/api/v1/auth/users/{{user_id}}`
- **Headers**:
  ```
  Authorization: Bearer <access_token>
  ```
- **Body**: None
- **Expected Response**:
```json
{{
  "success": true,
  "message": "User deactivated successfully"
}}
```

#### 3.5 List Users
  ```
  Authorization: Bearer <access_token>
  ```
- **Query Parameters**:
  - `hotel_id` (optional): Filter by hotel ID
  - `branch_id` (optional): Filter by branch ID
  - `role` (optional): Filter by role name
  - `is_active` (optional): Filter by active status
  - `page` (optional): Page number (default: 1)
  - `per_page` (optional): Items per page (default: 10, max: 100)
- **Body**: None
- **Expected Response**:
```json
{{
  "success": true,
  "message": "Users retrieved successfully",
  "data": {{
    "users": [
      {{
        "id": 1,
        "username": "admin@hotel.com",
        "role": "admin",
        "hotel_id": 1,
        "branch_id": 1,
        "is_active": true,
        "created_at": "2025-01-09T10:30:00Z"
      }}
    ],
    "total": 1,
    "page": 1,
    "per_page": 10
  }}
}}
```


### 4. Password Management

#### 4.1 Forgot Password
- **URL**: `{base_url}/api/v1/auth/forgot-password`
- **Description**: Initiates the forgot password flow. An email with a reset token will be sent to the user's `contact_email`.
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "username": "some_user@example.com"
}}
```
- **Expected Response**:
```json
{{
  "message": "If an account with that username exists, a password reset link has been sent to the associated email address."
}}
```

#### 4.2 Reset Password (after forgot)
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/reset-password-forgot`
- **Description**: Completes the forgot password flow by setting a new password using the token from the email.
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "username": "some_user@example.com",
  "token": "PASTE_TOKEN_FROM_EMAIL_HERE",
  "new_password": "NewSecurePassword123!"
}}
```
- **Expected Response**:
```json
{{
  "message": "Password has been reset successfully."
}}
```

#### 4.3 First-Time Password Reset
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/reset-password`
- **Description**: For a newly created user to set their permanent password. Requires the one-time password and the token from the welcome email.
- **Headers**:
  ```
  Content-Type: application/json
  ```
- **Body** (raw JSON):
```json
{{
  "username": "new_user@example.com",
  "current_password": "FirstNameWelcome",
  "new_password": "NewSecurePassword123!",
  "token": "PASTE_TOKEN_FROM_WELCOME_EMAIL"
}}
```
- **Expected Response**:
```json
{{
  "message": "Password has been reset successfully."
}}
```

#### 4.4 Verify Reset Token
- **Method**: POST
- **URL**: `{base_url}/api/v1/auth/verify-reset-token?token=<token>`
- **Description**: A helper endpoint to check if a token is valid before the user attempts to reset their password.
- **Headers**: None
- **Body**: None
- **Expected Response**:
```json
{{
  "is_valid": true,
  "message": "Token is valid."
}}
```


## Error Responses

All endpoints may return error responses in the following format:

### 400 Bad Request
```json
{{
  "error_code": "VALIDATION_ERROR",
  "message": "Data validation failed",
  "details": "Specific validation error details",
  "timestamp": "2025-01-09T10:30:00Z"
}}
```

### 401 Unauthorized
```json
{{
  "error_code": "AUTHENTICATION_ERROR",
  "message": "Authentication failed",
  "timestamp": "2025-01-09T10:30:00Z"
}}
```

### 403 Forbidden
```json
{{
  "error_code": "AUTHORIZATION_ERROR",
  "message": "Access denied",
  "timestamp": "2025-01-09T10:30:00Z"
}}
```

### 404 Not Found
```json
{{
  "error_code": "HTTP_404",
  "message": "Resource not found",
  "timestamp": "2025-01-09T10:30:00Z"
}}
```

### 422 Unprocessable Entity
```json
{{
  "error_code": "REQUEST_VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [
    {{
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }}
  ],
  "timestamp": "2025-01-09T10:30:00Z"
}}
```

### 429 Too Many Requests
```json
{{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests",
  "timestamp": "2025-01-09T10:30:00Z"
}}
```

### 500 Internal Server Error
```json
{{
  "error_code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred",
  "timestamp": "2025-01-09T10:30:00Z"
}}
```

---

## Postman Collection Import

To import these endpoints into Postman:

1. Copy the JSON structure for each endpoint
2. Create a new collection in Postman
3. Add requests manually or use the Postman API import feature
4. Set up environment variables for:
   - `base_url`: {base_url}
   - `access_token`: Your JWT access token
   - `refresh_token`: Your JWT refresh token

## Authentication Flow

1. **Login**: Use endpoint 2.1 to get access and refresh tokens
2. **Use API**: Include access token in Authorization header for protected endpoints
3. **Refresh**: Use endpoint 2.2 when access token expires
4. **Logout**: Use endpoint 2.3 to invalidate tokens

## Rate Limiting

- Authentication endpoints: 5 requests per minute per IP
- General endpoints: 60 requests per minute per user
- Brute force protection: Account locked after 5 failed login attempts

---

*This API documentation was generated automatically by the HotelAgent validation system.*
"""
        
        return content
    
    def _create_troubleshooting_content(self) -> str:
        """
        Create troubleshooting.md content.
        
        Returns:
            Troubleshooting documentation content
        """
        content = f"""# HotelAgent Backend Troubleshooting Guide

Generated on: {datetime.now().isoformat()}

## Common Issues and Solutions

### 1. Installation Issues

#### Python Version Compatibility
**Problem**: ImportError or syntax errors during startup
**Solution**:
```powershell
# Check Python version
python --version

# Ensure Python 3.11+ is installed
# Download from: https://www.python.org/downloads/
```

#### Virtual Environment Issues
**Problem**: Cannot activate virtual environment
**Solution**:
```powershell
# Check execution policy
Get-ExecutionPolicy

# Set execution policy if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Recreate virtual environment if corrupted
Remove-Item -Recurse -Force venv
python -m venv venv
.\\venv\\Scripts\\Activate.ps1
```

#### Package Installation Failures
**Problem**: pip install fails with permission or network errors
**Solution**:
```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install with user flag if permission issues
pip install --user -r requirements.txt

# Use different index if network issues
pip install -i https://pypi.org/simple/ -r requirements.txt

# Clear pip cache
pip cache purge
```

### 2. Database Connection Issues

#### PostgreSQL Connection Failed
**Problem**: `psycopg2.OperationalError: could not connect to server`
**Solution**:
```powershell
# Check if PostgreSQL is running
Get-Service -Name postgresql*

# Start PostgreSQL service
Start-Service postgresql-x64-14

# Test connection
psql -U postgres -h localhost -p 5432 -c "SELECT version();"

# Check DATABASE_URL in .env file
# Format: postgresql://username:password@localhost:5432/database_name
```

#### Supabase Connection Issues
**Problem**: Connection timeout or authentication errors
**Solution**:
```powershell
# Verify Supabase credentials in .env
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-supabase-anon-key
# DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres

# Test connection
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
print('Connection successful')
"
```

#### Migration Issues
**Problem**: Alembic migration errors
**Solution**:
```powershell
# Check current migration status
alembic current

# Reset migrations (CAUTION: This will lose data)
alembic downgrade base
alembic upgrade head

# Create new migration if schema changes
alembic revision --autogenerate -m "Fix schema"

# Manual migration fix
alembic edit <revision_id>
```

### 3. Redis Connection Issues

#### Redis Server Not Running
**Problem**: `redis.exceptions.ConnectionError`
**Solution**:
```powershell
# Check if Redis is running
Get-Process -Name redis-server -ErrorAction SilentlyContinue

# Start Redis server (Windows)
redis-server

# Test Redis connection
redis-cli ping

# Check REDIS_URL in .env
# Format: redis://localhost:6379/0
```

#### Redis Authentication Issues
**Problem**: `NOAUTH Authentication required`
**Solution**:
```powershell
# Update REDIS_URL with password
# redis://username:password@localhost:6379/0

# Or disable authentication in redis.conf
# Comment out: requirepass your_password
```

### 4. Application Startup Issues

#### Port Already in Use
**Problem**: `OSError: [WinError 10048] Only one usage of each socket address`
**Solution**:
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process by PID
taskkill /PID <process_id> /F

# Use different port
uvicorn app.main:app --port 8001
```

#### Environment Variables Not Loaded
**Problem**: KeyError for environment variables
**Solution**:
```powershell
# Check .env file exists and has correct format
Get-Content .env

# Verify environment variables are loaded
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('DATABASE_URL:', os.getenv('DATABASE_URL'))
print('REDIS_URL:', os.getenv('REDIS_URL'))
"

# Manually set environment variables
$env:DATABASE_URL = "postgresql://..."
$env:REDIS_URL = "redis://..."
```

#### Import Errors
**Problem**: `ModuleNotFoundError` or import issues
**Solution**:
```powershell
# Check if in correct directory
Get-Location

# Ensure virtual environment is activated
.\\venv\\Scripts\\Activate.ps1

# Reinstall requirements
pip install -r requirements.txt

# Check Python path
python -c "import sys; print('\\n'.join(sys.path))"
```

### 5. Authentication Issues

#### JWT Token Issues
**Problem**: Invalid token or token expired errors
**Solution**:
```powershell
# Check JWT_SECRET_KEY in .env
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Verify token expiration settings
# JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
# JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Clear Redis token cache
redis-cli FLUSHDB
```

#### Login Failures
**Problem**: Invalid credentials or account locked
**Solution**:
```powershell
# Check user exists in database
python -c "
from app.core.database import get_db
from app.models.core.user import User
from sqlalchemy.orm import Session

db = next(get_db())
user = db.query(User).filter(User.email == 'admin@example.com').first()
print(f'User found: {{user is not None}}')
if user:
    print(f'Active: {{user.is_active}}')
"

# Reset user password
python scripts/reset_password.py admin@example.com

# Clear brute force protection
redis-cli DEL "brute_force:admin@example.com"
```

### 6. Performance Issues

#### Slow Database Queries
**Problem**: High response times
**Solution**:
```powershell
# Enable query logging in PostgreSQL
# Add to postgresql.conf:
# log_statement = 'all'
# log_min_duration_statement = 1000

# Check database connections
# PostgreSQL: SELECT * FROM pg_stat_activity;

# Add database indexes
alembic revision -m "Add performance indexes"
```

#### High Memory Usage
**Problem**: Application consuming too much memory
**Solution**:
```powershell
# Monitor memory usage
Get-Process -Name python | Select-Object WorkingSet, VirtualMemorySize

# Reduce worker processes
# gunicorn app.main:app -w 2

# Check for memory leaks
pip install memory-profiler
python -m memory_profiler app/main.py
```

### 7. CORS Issues

#### Frontend Cannot Access API
**Problem**: CORS policy errors in browser
**Solution**:
```powershell
# Update CORS_ORIGINS in .env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080", "https://yourdomain.com"]

# Enable credentials if needed
CORS_ALLOW_CREDENTIALS=true

# Allow all origins for development (NOT for production)
CORS_ORIGINS=["*"]
```

### 8. SSL/HTTPS Issues

#### SSL Certificate Errors
**Problem**: SSL handshake failures
**Solution**:
```powershell
# Generate self-signed certificate for development
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Run with HTTPS
uvicorn app.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem

# For production, use proper SSL certificates
# Let's Encrypt: https://letsencrypt.org/
```

### 9. Logging and Debugging

#### Enable Debug Logging
```powershell
# Set DEBUG=true in .env
DEBUG=true
LOG_LEVEL=DEBUG

# View logs in real-time
Get-Content -Path "logs/app.log" -Tail 50 -Wait

# Enable SQL query logging
# Add to .env:
SQLALCHEMY_ECHO=true
```

#### Debug Mode
```powershell
# Run with debug mode
uvicorn app.main:app --reload --log-level debug

# Use Python debugger
python -m pdb -m uvicorn app.main:app
```

### 10. Docker Issues

#### Docker Build Failures
**Problem**: Docker build fails
**Solution**:
```powershell
# Clean Docker cache
docker system prune -a

# Build with no cache
docker build --no-cache -t hotelagent-backend .

# Check Dockerfile syntax
docker build --dry-run -t hotelagent-backend .
```

#### Container Networking Issues
**Problem**: Cannot connect to database from container
**Solution**:
```powershell
# Use host networking for development
docker run --network host hotelagent-backend

# Update DATABASE_URL for container
# Use host.docker.internal instead of localhost
DATABASE_URL=postgresql://postgres:password@host.docker.internal:5432/hotelagent
```

## Diagnostic Commands

### System Health Check
```powershell
# Run comprehensive health check
python validation/main.py --check-all

# Check individual components
python -c "
from app.core.database import get_db
from app.core.redis import get_redis
print('Database:', next(get_db()) is not None)
print('Redis:', get_redis().ping())
"
```

### Performance Monitoring
```powershell
# Monitor system resources
Get-Counter "\\Process(python)\\% Processor Time"
Get-Counter "\\Process(python)\\Working Set"

# Monitor database performance
# PostgreSQL: SELECT * FROM pg_stat_statements;
```

### Log Analysis
```powershell
# Search for errors in logs
Select-String -Path "logs/*.log" -Pattern "ERROR|CRITICAL"

# Monitor authentication failures
Select-String -Path "logs/auth.log" -Pattern "login_failed"

# Check rate limiting
Select-String -Path "logs/app.log" -Pattern "rate_limit"
```

## Getting Help

### Log Collection
When reporting issues, collect these logs:
```powershell
# Application logs
Get-Content logs/app.log | Out-File debug_app.log

# System information
Get-ComputerInfo | Out-File debug_system.log

# Environment variables (remove sensitive data)
Get-ChildItem Env: | Out-File debug_env.log

# Package versions
pip list | Out-File debug_packages.log
```

### Support Channels
- GitHub Issues: [Repository URL]
- Documentation: See README.md and setup.md
- Email: [Support email]

---

*This troubleshooting guide was generated automatically by the HotelAgent validation system.*
"""
        
        return content