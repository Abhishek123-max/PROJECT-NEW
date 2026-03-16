#!/usr/bin/env python3
"""
Demo script for the HotelAgent Backend Validation System.

This script demonstrates the validation system capabilities without requiring
all services to be running.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from validation.main import SystemValidator
from validation.models import ValidationResult, ValidationStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print a nice banner for the demo."""
    print("\n" + "="*70)
    print("🏨 HOTELAGENT BACKEND VALIDATION SYSTEM DEMO")
    print("="*70)
    print("This demo shows the validation system capabilities.")
    print("Note: Some tests may fail if services are not running locally.")
    print("-"*70)


async def demo_validation_models():
    """Demonstrate the validation models."""
    print("\n📋 VALIDATION MODELS DEMO")
    print("-" * 40)
    
    # Create sample validation results
    success_result = ValidationResult(
        component="demo",
        test_name="sample_success_test",
        status=ValidationStatus.SUCCESS,
        message="This is a successful test result",
        details={"response_time": "0.123s", "status_code": 200},
        suggestions=[]
    )
    
    warning_result = ValidationResult(
        component="demo",
        test_name="sample_warning_test",
        status=ValidationStatus.WARNING,
        message="This is a warning test result",
        details={"issue": "Minor configuration issue"},
        suggestions=["Consider updating configuration", "Review best practices"]
    )
    
    error_result = ValidationResult(
        component="demo",
        test_name="sample_error_test",
        status=ValidationStatus.ERROR,
        message="This is an error test result",
        details={"error": "Connection refused", "error_type": "ConnectionError"},
        suggestions=["Check if service is running", "Verify network connectivity"]
    )
    
    # Display results
    results = [success_result, warning_result, error_result]
    for result in results:
        status_icon = {
            ValidationStatus.SUCCESS: "✅",
            ValidationStatus.WARNING: "⚠️",
            ValidationStatus.ERROR: "❌"
        }[result.status]
        
        print(f"{status_icon} {result.component}.{result.test_name}")
        print(f"   Message: {result.message}")
        if result.suggestions:
            print(f"   Suggestions: {', '.join(result.suggestions[:2])}")
        print()


async def demo_individual_validators():
    """Demonstrate individual validator components."""
    print("\n🔧 INDIVIDUAL VALIDATORS DEMO")
    print("-" * 40)
    
    # Backend Validator Demo
    print("1. Backend Validator")
    from validation.backend_validator import BackendValidator
    
    backend_validator = BackendValidator("http://localhost:8000")
    print(f"   ✅ Initialized with base URL: {backend_validator.base_url}")
    print(f"   📊 Configured to test {len(backend_validator.endpoints)} endpoints")
    
    # Redis Validator Demo
    print("\n2. Redis Validator")
    from validation.redis_validator import RedisValidator
    
    redis_validator = RedisValidator("redis://localhost:6379/0")
    print(f"   ✅ Initialized with Redis URL: {redis_validator.redis_url}")
    print("   🔴 Ready to test connection, CRUD operations, and session management")
    
    # Database Validator Demo
    print("\n3. Database Validator")
    from validation.database_validator import DatabaseValidator
    
    database_url = "postgresql+asyncpg://demo:demo@localhost:5432/demo"
    database_validator = DatabaseValidator(database_url)
    print(f"   ✅ Initialized with database URL: postgresql://demo:***@localhost:5432/demo")
    print(f"   🐘 Configured to validate {len(database_validator.expected_tables)} tables")
    
    # List expected tables
    print("   Expected tables:")
    for table in database_validator.expected_tables[:3]:  # Show first 3
        print(f"     - {table.name}: {table.description}")
    print(f"     ... and {len(database_validator.expected_tables) - 3} more")


async def demo_system_validator():
    """Demonstrate the complete system validator."""
    print("\n🚀 SYSTEM VALIDATOR DEMO")
    print("-" * 40)
    
    # Initialize system validator
    validator = SystemValidator(
        base_url="http://localhost:8000",
        redis_url="redis://localhost:6379/0",
        database_url="postgresql+asyncpg://demo:demo@localhost:5432/demo"
    )
    
    print("✅ System validator initialized with:")
    print(f"   🌐 Backend URL: {validator.base_url}")
    print(f"   🔴 Redis URL: {validator.redis_url}")
    print(f"   🐘 Database URL: postgresql://demo:***@localhost:5432/demo")
    
    print("\n📊 Validation capabilities:")
    print("   ✅ FastAPI backend health and endpoint testing")
    print("   ✅ Redis connectivity and operations testing")
    print("   ✅ PostgreSQL database and schema validation")
    print("   ✅ Parallel execution for faster results")
    print("   ✅ Comprehensive error detection and suggestions")
    print("   ✅ JSON report generation")
    
    # Show what a validation run would do (without actually running it)
    print("\n🔄 A full validation run would:")
    print("   1. Test FastAPI server health and all API endpoints")
    print("   2. Validate Redis connection and CRUD operations")
    print("   3. Check database connectivity and schema")
    print("   4. Generate detailed report with suggestions")
    print("   5. Provide system health assessment")


async def demo_cli_usage():
    """Demonstrate CLI usage examples."""
    print("\n💻 CLI USAGE EXAMPLES")
    print("-" * 40)
    
    examples = [
        ("Basic validation", "python -m validation.cli"),
        ("Skip Redis testing", "python -m validation.cli --skip-redis"),
        ("Generate report", "python -m validation.cli --output report.json"),
        ("Custom URLs", "python -m validation.cli --base-url http://localhost:8080"),
        ("Strict mode", "python -m validation.cli --strict"),
        ("Sequential execution", "python -m validation.cli --sequential"),
        ("Quiet mode", "python -m validation.cli --quiet"),
        ("Debug mode", "python -m validation.cli --debug")
    ]
    
    for description, command in examples:
        print(f"   {description}:")
        print(f"     {command}")
        print()


async def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n🛠️  ERROR HANDLING DEMO")
    print("-" * 40)
    
    print("The validation system provides intelligent error detection:")
    print()
    
    error_scenarios = [
        ("Backend not running", [
            "Start the FastAPI server using: uvicorn app.main:app --reload",
            "Check if the server is running on the correct port",
            "Verify network connectivity"
        ]),
        ("Redis connection failed", [
            "Start Redis server: redis-server",
            "Check if Redis is running on the correct port",
            "Verify Redis connection URL in configuration"
        ]),
        ("Database connection failed", [
            "Start PostgreSQL service",
            "Check database username and password",
            "Verify database exists"
        ]),
        ("Missing database tables", [
            "Run database migrations: alembic upgrade head",
            "Check migration files for table creation",
            "Verify database schema"
        ])
    ]
    
    for scenario, suggestions in error_scenarios:
        print(f"❌ {scenario}:")
        for suggestion in suggestions[:2]:  # Show first 2 suggestions
            print(f"   💡 {suggestion}")
        print()


async def main():
    """Main demo function."""
    try:
        print_banner()
        
        # Run demo sections
        await demo_validation_models()
        await demo_individual_validators()
        await demo_system_validator()
        await demo_cli_usage()
        await demo_error_handling()
        
        # Final message
        print("\n" + "="*70)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("The HotelAgent Backend Validation System is ready to use.")
        print()
        print("To run actual validation:")
        print("  python -m validation.cli")
        print()
        print("To run with your configuration:")
        print("  python -m validation.cli --database-url YOUR_DB_URL")
        print()
        print("For help:")
        print("  python -m validation.cli --help")
        print("="*70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)