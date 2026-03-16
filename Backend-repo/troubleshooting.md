# HotelAgent Backend Troubleshooting Guide

Generated on: 2025-09-18T15:54:57.552446

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
.\venv\Scripts\Activate.ps1
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
.\venv\Scripts\Activate.ps1

# Reinstall requirements
pip install -r requirements.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
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
print(f'User found: {user is not None}')
if user:
    print(f'Active: {user.is_active}')
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
Get-Counter "\Process(python)\% Processor Time"
Get-Counter "\Process(python)\Working Set"

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
