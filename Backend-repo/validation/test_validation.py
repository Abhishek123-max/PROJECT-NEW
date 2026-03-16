"""
Test script for the Backend Validation System.

This script demonstrates how to use the validation system programmatically.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation.main import SystemValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_individual_components():
    """Test individual validation components."""
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL VALIDATION COMPONENTS")
    print("="*60)
    
    # Test backend validator
    print("\n1. Testing Backend Validator...")
    from validation.backend_validator import BackendValidator
    
    backend_validator = BackendValidator("http://localhost:8000")
    backend_results = await backend_validator.validate_all()
    
    print(f"Backend validation completed: {len(backend_results)} tests")
    for result in backend_results[:3]:  # Show first 3 results
        status_icon = "✅" if result.status.value == "success" else "❌" if result.status.value == "error" else "⚠️"
        print(f"  {status_icon} {result.test_name}: {result.message}")
    
    # Test Redis validator
    print("\n2. Testing Redis Validator...")
    from validation.redis_validator import RedisValidator
    
    redis_validator = RedisValidator("redis://localhost:6379/0")
    redis_results = await redis_validator.validate_all()
    
    print(f"Redis validation completed: {len(redis_results)} tests")
    for result in redis_results[:3]:  # Show first 3 results
        status_icon = "✅" if result.status.value == "success" else "❌" if result.status.value == "error" else "⚠️"
        print(f"  {status_icon} {result.test_name}: {result.message}")
    
    # Test Database validator (if DATABASE_URL is available)
    database_url = "postgresql+asyncpg://postgres:nxLXK7s!2jBSUb#@db.qehvovlcvrvkxxeuduho.supabase.co:5432/postgres"
    
    if database_url:
        print("\n3. Testing Database Validator...")
        from validation.database_validator import DatabaseValidator
        
        database_validator = DatabaseValidator(database_url)
        database_results = await database_validator.validate_all()
        
        print(f"Database validation completed: {len(database_results)} tests")
        for result in database_results[:3]:  # Show first 3 results
            status_icon = "✅" if result.status.value == "success" else "❌" if result.status.value == "error" else "⚠️"
            print(f"  {status_icon} {result.test_name}: {result.message}")
    else:
        print("\n3. Skipping Database Validator (no DATABASE_URL)")


async def test_system_validator():
    """Test the complete system validator."""
    print("\n" + "="*60)
    print("TESTING COMPLETE SYSTEM VALIDATOR")
    print("="*60)
    
    # Initialize system validator
    validator = SystemValidator(
        base_url="http://localhost:8000",
        redis_url="redis://localhost:6379/0",
        database_url="postgresql+asyncpg://postgres:nxLXK7s!2jBSUb#@db.qehvovlcvrvkxxeuduho.supabase.co:5432/postgres"
    )
    
    # Run full validation
    print("\nRunning full system validation...")
    summary = await validator.run_full_validation()
    
    # Print summary
    validator.print_summary()
    
    # Generate and save report
    report_file = "validation_test_report.json"
    report = validator.generate_report(report_file)
    print(f"\nDetailed report saved to: {report_file}")
    
    return summary


async def test_error_handling():
    """Test error handling with invalid configurations."""
    print("\n" + "="*60)
    print("TESTING ERROR HANDLING")
    print("="*60)
    
    # Test with invalid URLs
    print("\n1. Testing with invalid backend URL...")
    validator = SystemValidator(
        base_url="http://localhost:9999",  # Invalid port
        redis_url="redis://localhost:6379/0",
        database_url="postgresql+asyncpg://invalid:invalid@localhost:5432/invalid"
    )
    
    summary = await validator.run_full_validation()
    print(f"Validation with invalid URLs: {summary.errors} errors, {summary.warnings} warnings")
    
    # Test with missing services
    print("\n2. Testing with missing Redis...")
    validator = SystemValidator(
        base_url="http://localhost:8000",
        redis_url="redis://localhost:9999/0",  # Invalid Redis port
        database_url=None  # No database
    )
    
    summary = await validator.run_full_validation(include_database=False)
    print(f"Validation with missing Redis: {summary.errors} errors, {summary.warnings} warnings")


async def main():
    """Main test function."""
    print("HotelAgent Backend Validation System - Test Suite")
    print("=" * 60)
    
    try:
        # Test individual components
        await test_individual_components()
        
        # Test complete system validator
        summary = await test_system_validator()
        
        # Test error handling
        await test_error_handling()
        
        print("\n" + "="*60)
        print("TEST SUITE COMPLETED")
        print("="*60)
        
        if summary.errors > 0:
            print(f"⚠️  System has {summary.errors} errors that need attention")
            return 1
        elif summary.warnings > 0:
            print(f"ℹ️  System has {summary.warnings} warnings")
            return 0
        else:
            print("✅ All validations passed successfully!")
            return 0
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)