"""
Command Line Interface for the Backend Validation System.

Provides easy-to-use CLI commands for running system validations.
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Optional

# Add the parent directory to the path so we can import from the app
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation.main import SystemValidator
from app.settings.base import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_environment_config() -> dict:
    """Load configuration from environment variables or settings."""
    try:
        settings = get_settings()
        return {
            "database_url": settings.DATABASE_URL,
            "redis_url": settings.REDIS_URL,
            "base_url": "http://localhost:8000"  # Default for local development
        }
    except Exception as e:
        logger.warning(f"Could not load settings: {e}")
        # Fallback to environment variables
        return {
            "database_url": os.getenv("DATABASE_URL"),
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "base_url": os.getenv("BASE_URL", "http://localhost:8000")
        }


async def run_validation(args):
    """Run the validation with the provided arguments."""
    # Load configuration
    config = load_environment_config()
    
    # Override with command line arguments if provided
    base_url = args.base_url or config["base_url"]
    redis_url = args.redis_url or config["redis_url"]
    database_url = args.database_url or config["database_url"]
    
    # Validate required configuration
    if not database_url:
        logger.error("Database URL is required. Set DATABASE_URL environment variable or use --database-url")
        return 1
    
    # Initialize validator
    validator = SystemValidator(
        base_url=base_url,
        redis_url=redis_url,
        database_url=database_url
    )
    
    # Run validation
    try:
        summary = await validator.run_full_validation(
            include_backend=not args.skip_backend,
            include_redis=not args.skip_redis,
            include_database=not args.skip_database,
            parallel=not args.sequential
        )
        
        # Print summary
        if not args.quiet:
            validator.print_summary()
        
        # Generate report if requested
        if args.output:
            report = validator.generate_report(args.output)
            if not args.quiet:
                print(f"\nDetailed report saved to: {args.output}")
        
        # Return appropriate exit code
        if summary.errors > 0:
            return 1  # Exit with error code if there are validation errors
        elif summary.warnings > 0:
            return 2 if args.strict else 0  # Exit with warning code in strict mode
        else:
            return 0  # Success
            
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="HotelAgent Backend Validation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full validation with default settings
  python -m validation.cli

  # Run only backend validation
  python -m validation.cli --skip-redis --skip-database

  # Run validation and save detailed report
  python -m validation.cli --output validation_report.json

  # Run validation with custom URLs
  python -m validation.cli --base-url http://localhost:8080 --redis-url redis://localhost:6380/0

  # Run validation in strict mode (warnings cause non-zero exit)
  python -m validation.cli --strict

  # Run validation sequentially (not in parallel)
  python -m validation.cli --sequential
        """
    )
    
    # Connection settings
    parser.add_argument(
        "--base-url",
        help="FastAPI server base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--redis-url",
        help="Redis connection URL (default: redis://localhost:6379/0)"
    )
    parser.add_argument(
        "--database-url",
        help="PostgreSQL database URL (required)"
    )
    
    # Component selection
    parser.add_argument(
        "--skip-backend",
        action="store_true",
        help="Skip FastAPI backend validation"
    )
    parser.add_argument(
        "--skip-redis",
        action="store_true",
        help="Skip Redis validation"
    )
    parser.add_argument(
        "--skip-database",
        action="store_true",
        help="Skip database validation"
    )
    
    # Execution options
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run validations sequentially instead of in parallel"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code on warnings"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        help="Save detailed validation report to JSON file"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress console output (except errors)"
    )
    
    # Logging options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Run validation
    try:
        exit_code = asyncio.run(run_validation(args))
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"CLI execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()