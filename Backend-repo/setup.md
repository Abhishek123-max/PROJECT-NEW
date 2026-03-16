# HotelAgent Backend Setup Guide

Generated on: 2025-09-18T15:54:57.547708

## Prerequisites

- Python 3.11.5 or higher
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
.\venv\Scripts\Activate.ps1

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

& "E:/RB Office/Hotel-Agent/venv/Scripts/Activate.ps1"

uvicorn app.main:app

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
CREATE EXTENSION IF NOT EXISTS pg_trgm;