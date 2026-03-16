# HotelAgent Backend Validation System

A comprehensive validation system for the HotelAgent FastAPI backend that validates server health, Redis connectivity, PostgreSQL database operations, and provides detailed error detection with automated fix suggestions.

## Features

### 🚀 FastAPI Backend Validation
- Server health checks and connectivity testing
- API endpoint validation with proper response verification
- Middleware testing (CORS, rate limiting, request validation)
- Error handling verification
- Response time monitoring

### 🔴 Redis Validation
- Connection testing and server info retrieval
- CRUD operations validation (SET, GET, DEL)
- Rate limiting functionality testing
- Session management validation
- Pipeline operations testing

### 🐘 PostgreSQL Database Validation
- Database connectivity and authentication testing
- Migration status verification
- Schema validation for all required tables
- CRUD operations testing
- Data segregation rules validation
- Transaction handling verification

### 📊 Comprehensive Reporting
- Detailed validation results with execution times
- Component-wise health assessment
- Automated fix suggestions for common issues
- JSON report generation
- System health scoring

## Installation

The validation system is part of the HotelAgent project. Ensure you have all dependencies installed:

```bash
cd hotel_agent
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Run the complete validation suite:

```bash
# Run full validation
python -m validation.cli

# Run with custom configuration
python -m validation.cli --base-url http://localhost:8080 --redis-url redis://localhost:6380/0

# Skip specific components
python -m validation.cli --skip-redis --skip-database

# Generate detailed report
python -m validation.cli --output validation_report.json

# Run in strict mode (warnings cause non-zero exit)
python -m validation.cli --strict

# Run sequentially instead of parallel
python -m validation.cli --sequential
```

### Programmatic Usage

```python
import asyncio
from validation.main import SystemValidator

async def run_validation():
    # Initialize validator
    validator = SystemValidator(
        base_url="http://localhost:8000",
        redis_url="redis://localhost:6379/0",
        database_url="postgresql+asyncpg://user:pass@localhost:5432/db"
    )
    
    # Run validation
    summary = await validator.run_full_validation()
    
    # Print results
    validator.print_summary()
    
    # Generate report
    report = validator.generate_report("validation_report.json")
    
    return summary

# Run the validation
summary = asyncio.run(run_validation())
```

### Individual Component Testing

```python
from validation.backend_validator import BackendValidator
from validation.redis_validator import RedisValidator
from validation.database_validator import DatabaseValidator

# Test only backend
backend_validator = BackendValidator("http://localhost:8000")
backend_results = await backend_validator.validate_all()

# Test only Redis
redis_validator = RedisValidator("redis://localhost:6379/0")
redis_results = await redis_validator.validate_all()

# Test only database
database_validator = DatabaseValidator("postgresql+asyncpg://...")
database_results = await database_validator.validate_all()
```

## Configuration

The validation system uses the same configuration as the main HotelAgent application:

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Optional: Custom base URL for API testing
BASE_URL=http://localhost:8000
```

### Settings Integration

The validator automatically loads configuration from the HotelAgent settings:

```python
from app.settings.base import get_settings

settings = get_settings()
# Uses settings.DATABASE_URL, settings.REDIS_URL, etc.
```

## Validation Tests

### Backend Tests
- `server_health_check`: Validates FastAPI server is running and responding
- `endpoint_*`: Tests all API endpoints for proper responses
- `cors_middleware`: Validates CORS configuration
- `validation_middleware`: Tests request validation
- `error_handling_404`: Verifies 404 error handling

### Redis Tests
- `connection_test`: Tests Redis server connectivity and info
- `crud_set_operation`: Validates SET operations
- `crud_get_operation`: Validates GET operations
- `crud_del_operation`: Validates DELETE operations
- `rate_limiting_counter`: Tests rate limiting functionality
- `session_storage`: Tests session data storage
- `session_retrieval`: Tests session data retrieval

### Database Tests
- `connection_test`: Tests PostgreSQL connectivity
- `migration_verification`: Checks Alembic migration status
- `table_validation_*`: Validates each required table exists
- `crud_select_operation`: Tests SELECT operations
- `transaction_handling`: Tests transaction support
- `data_segregation_*`: Validates data isolation rules

## Error Detection and Suggestions

The validation system provides automated suggestions for common issues:

### Backend Issues
- Server not running → Start with `uvicorn app.main:app --reload`
- Port conflicts → Check if port is already in use
- Configuration errors → Verify environment variables

### Redis Issues
- Connection failures → Start Redis with `redis-server`
- Authentication errors → Check Redis configuration
- Memory issues → Monitor Redis memory usage

### Database Issues
- Connection failures → Start PostgreSQL service
- Missing tables → Run `alembic upgrade head`
- Permission errors → Check database user permissions
- Migration issues → Verify Alembic configuration

## Report Format

The validation system generates comprehensive JSON reports:

```json
{
  "validation_report": {
    "timestamp": "2025-01-09 10:30:00",
    "summary": {
      "total_tests": 15,
      "passed": 12,
      "warnings": 2,
      "errors": 1,
      "success_rate": 80.0,
      "execution_time": 5.23
    },
    "components": {
      "backend": { "total_tests": 6, "passed": 5, "warnings": 1, "errors": 0 },
      "redis": { "total_tests": 5, "passed": 5, "warnings": 0, "errors": 0 },
      "database": { "total_tests": 4, "passed": 2, "warnings": 1, "errors": 1 }
    },
    "recommendations": [
      {
        "priority": "high",
        "category": "critical_issues",
        "title": "Critical Issues Requiring Immediate Attention",
        "suggestions": ["Run database migrations: alembic upgrade head"]
      }
    ],
    "system_health": {
      "status": "warning",
      "score": 80.0,
      "description": "System is functional but has some issues"
    }
  }
}
```

## Testing

Run the test suite to verify the validation system:

```bash
# Run test suite
python validation/test_validation.py

# Run with verbose output
python validation/test_validation.py --verbose
```

## Integration with CI/CD

The validation system returns appropriate exit codes for CI/CD integration:

- `0`: All validations passed
- `1`: Validation errors found
- `2`: Warnings found (only in strict mode)
- `130`: Interrupted by user

Example GitHub Actions integration:

```yaml
- name: Run Backend Validation
  run: |
    python -m validation.cli --output validation_report.json
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    REDIS_URL: ${{ secrets.REDIS_URL }}

- name: Upload Validation Report
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: validation-report
    path: validation_report.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the hotel_agent directory
   cd hotel_agent
   python -m validation.cli
   ```

2. **Connection Timeouts**
   ```bash
   # Check if services are running
   # FastAPI: curl http://localhost:8000/health
   # Redis: redis-cli ping
   # PostgreSQL: pg_isready
   ```

3. **Permission Errors**
   ```bash
   # Check database permissions
   # Verify Redis access
   # Check file system permissions for report generation
   ```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python -m validation.cli --debug
```

## Contributing

When adding new validation tests:

1. Follow the existing pattern in validator classes
2. Return `ValidationResult` objects with appropriate status
3. Include helpful error messages and suggestions
4. Add execution time tracking
5. Update this README with new test descriptions

## License

This validation system is part of the HotelAgent project and follows the same license terms.