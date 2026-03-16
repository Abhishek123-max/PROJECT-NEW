"""
Database Validator.

Validates PostgreSQL/Supabase connectivity, migrations, schema verification, and data segregation.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect

from .models import ValidationResult, ValidationStatus, DatabaseTable

logger = logging.getLogger(__name__)


class DatabaseValidator:
    """Validates PostgreSQL database functionality."""
    
    def __init__(self, database_url: str):
        """Initialize the database validator.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        
        # Define expected tables and their structure
        self.expected_tables = [
            DatabaseTable(
                name="users",
                required_columns=["id", "email", "password_hash", "role", "hotel_id", "branch_id", "is_active", "created_at"],
                description="User accounts with role-based access"
            ),
            DatabaseTable(
                name="roles",
                required_columns=["id", "name", "description", "level", "created_at"],
                description="Role definitions and hierarchy"
            ),
            DatabaseTable(
                name="hotels",
                required_columns=["id", "name", "address", "phone", "email", "is_active", "created_at"],
                description="Hotel information"
            ),
            DatabaseTable(
                name="branches",
                required_columns=["id", "hotel_id", "name", "address", "phone", "is_active", "created_at"],
                description="Hotel branches"
            ),
            DatabaseTable(
                name="audit_logs",
                required_columns=["id", "user_id", "action", "resource", "details", "ip_address", "created_at"],
                description="Audit trail for all user actions"
            ),
            DatabaseTable(
                name="alembic_version",
                required_columns=["version_num"],
                description="Database migration version tracking"
            )
        ]
    
    async def _get_engine(self):
        """Get SQLAlchemy async engine."""
        if self.engine is None:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600
            )
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
        return self.engine
    
    async def validate_all(self) -> List[ValidationResult]:
        """Run all database validations.
        
        Returns:
            List of validation results
        """
        results = []
        
        try:
            # Test connection
            results.extend(await self.test_connection())
            
            # Verify migrations
            results.extend(await self.verify_migrations())
            
            # Validate schema
            results.extend(await self.validate_tables())
            
            # Test CRUD operations
            results.extend(await self.test_crud_operations())
            
            # Validate data segregation
            results.extend(await self.validate_data_segregation())
            
        finally:
            # Clean up
            if self.engine:
                await self.engine.dispose()
        
        return results
    
    async def test_connection(self) -> List[ValidationResult]:
        """Test PostgreSQL database connection.
        
        Returns:
            List of validation results
        """
        results = []
        
        start_time = time.time()
        try:
            engine = await self._get_engine()
            
            async with engine.begin() as conn:
                # Test basic connection with a simple query
                result = await conn.execute(text("SELECT version(), current_database(), current_user"))
                row = result.fetchone()
                
                execution_time = time.time() - start_time
                
                if row:
                    version, database, user = row
                    results.append(ValidationResult(
                        component="database",
                        test_name="connection_test",
                        status=ValidationStatus.SUCCESS,
                        message="Database connection is working correctly",
                        details={
                            "postgresql_version": version,
                            "database_name": database,
                            "connected_user": user,
                            "response_time": f"{execution_time:.3f}s"
                        },
                        execution_time=execution_time
                    ))
                else:
                    results.append(ValidationResult(
                        component="database",
                        test_name="connection_test",
                        status=ValidationStatus.ERROR,
                        message="Database connection test returned no results",
                        details={},
                        suggestions=[
                            "Check database server status",
                            "Verify database connection parameters"
                        ],
                        execution_time=execution_time
                    ))
                    
        except asyncpg.exceptions.InvalidCatalogNameError as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="database",
                test_name="connection_test",
                status=ValidationStatus.ERROR,
                message="Database does not exist",
                details={"error": str(e)},
                suggestions=[
                    "Create the database using: CREATE DATABASE hotelagent_db;",
                    "Verify the database name in the connection URL",
                    "Check database server configuration"
                ],
                execution_time=execution_time
            ))
        except asyncpg.exceptions.InvalidPasswordError as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="database",
                test_name="connection_test",
                status=ValidationStatus.ERROR,
                message="Database authentication failed",
                details={"error": str(e)},
                suggestions=[
                    "Check database username and password",
                    "Verify database user permissions",
                    "Check connection URL format"
                ],
                execution_time=execution_time
            ))
        except asyncpg.exceptions.ConnectionDoesNotExistError as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="database",
                test_name="connection_test",
                status=ValidationStatus.ERROR,
                message="Cannot connect to database server",
                details={"error": str(e)},
                suggestions=[
                    "Start PostgreSQL server",
                    "Check if database server is running on the correct port",
                    "Verify network connectivity",
                    "Check firewall settings"
                ],
                execution_time=execution_time
            ))
        except Exception as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="database",
                test_name="connection_test",
                status=ValidationStatus.ERROR,
                message=f"Unexpected database connection error: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                suggestions=[
                    "Check database connection URL format",
                    "Verify database server configuration",
                    "Check database server logs"
                ],
                execution_time=execution_time
            ))
        
        return results
    
    async def verify_migrations(self) -> List[ValidationResult]:
        """Verify database migrations have been applied.
        
        Returns:
            List of validation results
        """
        results = []
        
        start_time = time.time()
        try:
            engine = await self._get_engine()
            
            async with engine.begin() as conn:
                # Check if alembic_version table exists
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'alembic_version'
                    )
                """))
                
                table_exists = result.scalar()
                
                if table_exists:
                    # Get current migration version
                    version_result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                    version_row = version_result.fetchone()
                    
                    execution_time = time.time() - start_time
                    
                    if version_row:
                        current_version = version_row[0]
                        results.append(ValidationResult(
                            component="database",
                            test_name="migration_verification",
                            status=ValidationStatus.SUCCESS,
                            message="Database migrations have been applied",
                            details={
                                "current_version": current_version,
                                "alembic_table_exists": True
                            },
                            execution_time=execution_time
                        ))
                    else:
                        results.append(ValidationResult(
                            component="database",
                            test_name="migration_verification",
                            status=ValidationStatus.WARNING,
                            message="Alembic version table exists but no version found",
                            details={"alembic_table_exists": True},
                            suggestions=[
                                "Run database migrations: alembic upgrade head",
                                "Check alembic configuration"
                            ],
                            execution_time=execution_time
                        ))
                else:
                    execution_time = time.time() - start_time
                    results.append(ValidationResult(
                        component="database",
                        test_name="migration_verification",
                        status=ValidationStatus.ERROR,
                        message="Alembic version table not found - migrations not initialized",
                        details={"alembic_table_exists": False},
                        suggestions=[
                            "Initialize alembic: alembic init alembic",
                            "Run initial migration: alembic upgrade head",
                            "Check alembic configuration files"
                        ],
                        execution_time=execution_time
                    ))
                    
        except Exception as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="database",
                test_name="migration_verification",
                status=ValidationStatus.ERROR,
                message=f"Error verifying migrations: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check database connection",
                    "Verify database permissions",
                    "Check alembic configuration"
                ],
                execution_time=execution_time
            ))
        
        return results
    
    async def validate_tables(self) -> List[ValidationResult]:
        """Validate that all required tables exist with correct schema.
        
        Returns:
            List of validation results
        """
        results = []
        
        try:
            engine = await self._get_engine()
            
            async with engine.begin() as conn:
                # Get all tables in the database
                tables_result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                
                existing_tables = [row[0] for row in tables_result.fetchall()]
                
                # Check each expected table
                for expected_table in self.expected_tables:
                    start_time = time.time()
                    
                    if expected_table.name in existing_tables:
                        # Table exists, check columns
                        columns_result = await conn.execute(text("""
                            SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns
                            WHERE table_schema = 'public' 
                            AND table_name = :table_name
                            ORDER BY ordinal_position
                        """), {"table_name": expected_table.name})
                        
                        existing_columns = [row[0] for row in columns_result.fetchall()]
                        missing_columns = [col for col in expected_table.required_columns if col not in existing_columns]
                        
                        execution_time = time.time() - start_time
                        
                        if not missing_columns:
                            results.append(ValidationResult(
                                component="database",
                                test_name=f"table_validation_{expected_table.name}",
                                status=ValidationStatus.SUCCESS,
                                message=f"Table '{expected_table.name}' exists with all required columns",
                                details={
                                    "table_name": expected_table.name,
                                    "required_columns": expected_table.required_columns,
                                    "existing_columns": existing_columns,
                                    "description": expected_table.description
                                },
                                execution_time=execution_time
                            ))
                        else:
                            results.append(ValidationResult(
                                component="database",
                                test_name=f"table_validation_{expected_table.name}",
                                status=ValidationStatus.ERROR,
                                message=f"Table '{expected_table.name}' is missing required columns",
                                details={
                                    "table_name": expected_table.name,
                                    "missing_columns": missing_columns,
                                    "existing_columns": existing_columns
                                },
                                suggestions=[
                                    "Run database migrations: alembic upgrade head",
                                    "Check migration files for table creation",
                                    "Verify database schema"
                                ],
                                execution_time=execution_time
                            ))
                    else:
                        execution_time = time.time() - start_time
                        results.append(ValidationResult(
                            component="database",
                            test_name=f"table_validation_{expected_table.name}",
                            status=ValidationStatus.ERROR,
                            message=f"Required table '{expected_table.name}' does not exist",
                            details={
                                "table_name": expected_table.name,
                                "description": expected_table.description,
                                "existing_tables": existing_tables
                            },
                            suggestions=[
                                "Run database migrations: alembic upgrade head",
                                "Create migration for missing table",
                                "Check database schema setup"
                            ],
                            execution_time=execution_time
                        ))
                        
        except Exception as e:
            results.append(ValidationResult(
                component="database",
                test_name="table_validation",
                status=ValidationStatus.ERROR,
                message=f"Error validating database tables: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check database connection",
                    "Verify database permissions",
                    "Check database schema"
                ],
                execution_time=0.0
            ))
        
        return results
    
    async def test_crud_operations(self) -> List[ValidationResult]:
        """Test basic CRUD operations on core tables.
        
        Returns:
            List of validation results
        """
        results = []
        
        try:
            engine = await self._get_engine()
            
            # Test if we can perform basic operations on the users table
            start_time = time.time()
            try:
                async with engine.begin() as conn:
                    # Test SELECT operation
                    select_result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                    user_count = select_result.scalar()
                    
                    execution_time = time.time() - start_time
                    
                    results.append(ValidationResult(
                        component="database",
                        test_name="crud_select_operation",
                        status=ValidationStatus.SUCCESS,
                        message="Database SELECT operation is working correctly",
                        details={
                            "table": "users",
                            "operation": "SELECT COUNT(*)",
                            "result": user_count
                        },
                        execution_time=execution_time
                    ))
                    
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="database",
                    test_name="crud_select_operation",
                    status=ValidationStatus.ERROR,
                    message=f"Error performing SELECT operation: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check if users table exists",
                        "Verify database permissions",
                        "Run database migrations"
                    ],
                    execution_time=execution_time
                ))
            
            # Test transaction handling
            start_time = time.time()
            try:
                async with engine.begin() as conn:
                    # Start a transaction and roll it back
                    await conn.execute(text("SELECT 1"))
                    # Transaction will be rolled back automatically
                    
                    execution_time = time.time() - start_time
                    
                    results.append(ValidationResult(
                        component="database",
                        test_name="transaction_handling",
                        status=ValidationStatus.SUCCESS,
                        message="Database transaction handling is working correctly",
                        details={
                            "operation": "transaction_test"
                        },
                        execution_time=execution_time
                    ))
                    
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="database",
                    test_name="transaction_handling",
                    status=ValidationStatus.ERROR,
                    message=f"Error testing transaction handling: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check database connection stability",
                        "Verify transaction support"
                    ],
                    execution_time=execution_time
                ))
                
        except Exception as e:
            results.append(ValidationResult(
                component="database",
                test_name="crud_operations",
                status=ValidationStatus.ERROR,
                message=f"Error setting up CRUD operations test: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check database connection",
                    "Verify database is properly initialized"
                ],
                execution_time=0.0
            ))
        
        return results
    
    async def validate_data_segregation(self) -> List[ValidationResult]:
        """Validate data segregation rules are enforced.
        
        Returns:
            List of validation results
        """
        results = []
        
        try:
            engine = await self._get_engine()
            
            # Test hotel-based data segregation
            start_time = time.time()
            try:
                async with engine.begin() as conn:
                    # Check if hotels table exists and has data
                    hotels_result = await conn.execute(text("SELECT COUNT(*) FROM hotels"))
                    hotel_count = hotels_result.scalar()
                    
                    if hotel_count > 0:
                        # Check if users are properly associated with hotels
                        users_with_hotels = await conn.execute(text("""
                            SELECT COUNT(*) FROM users 
                            WHERE hotel_id IS NOT NULL
                        """))
                        users_with_hotel_count = users_with_hotels.scalar()
                        
                        # Check total users
                        total_users = await conn.execute(text("SELECT COUNT(*) FROM users"))
                        total_user_count = total_users.scalar()
                        
                        execution_time = time.time() - start_time
                        
                        if users_with_hotel_count == total_user_count and total_user_count > 0:
                            results.append(ValidationResult(
                                component="database",
                                test_name="data_segregation_hotel_association",
                                status=ValidationStatus.SUCCESS,
                                message="All users are properly associated with hotels",
                                details={
                                    "total_hotels": hotel_count,
                                    "total_users": total_user_count,
                                    "users_with_hotels": users_with_hotel_count
                                },
                                execution_time=execution_time
                            ))
                        elif total_user_count == 0:
                            results.append(ValidationResult(
                                component="database",
                                test_name="data_segregation_hotel_association",
                                status=ValidationStatus.WARNING,
                                message="No users found to validate data segregation",
                                details={
                                    "total_hotels": hotel_count,
                                    "total_users": total_user_count
                                },
                                suggestions=[
                                    "Add test users to validate data segregation",
                                    "Run database seeding scripts"
                                ],
                                execution_time=execution_time
                            ))
                        else:
                            results.append(ValidationResult(
                                component="database",
                                test_name="data_segregation_hotel_association",
                                status=ValidationStatus.WARNING,
                                message="Some users are not associated with hotels",
                                details={
                                    "total_hotels": hotel_count,
                                    "total_users": total_user_count,
                                    "users_with_hotels": users_with_hotel_count,
                                    "users_without_hotels": total_user_count - users_with_hotel_count
                                },
                                suggestions=[
                                    "Review user creation process",
                                    "Ensure hotel_id is required for users",
                                    "Check data integrity constraints"
                                ],
                                execution_time=execution_time
                            ))
                    else:
                        execution_time = time.time() - start_time
                        results.append(ValidationResult(
                            component="database",
                            test_name="data_segregation_hotel_association",
                            status=ValidationStatus.WARNING,
                            message="No hotels found to validate data segregation",
                            details={"total_hotels": hotel_count},
                            suggestions=[
                                "Add test hotels to validate data segregation",
                                "Run database seeding scripts",
                                "Check hotel table setup"
                            ],
                            execution_time=execution_time
                        ))
                        
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="database",
                    test_name="data_segregation_hotel_association",
                    status=ValidationStatus.ERROR,
                    message=f"Error validating hotel-based data segregation: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check if hotels and users tables exist",
                        "Verify database schema",
                        "Check foreign key constraints"
                    ],
                    execution_time=execution_time
                ))
            
            # Test branch-based data segregation
            start_time = time.time()
            try:
                async with engine.begin() as conn:
                    # Check if branches are properly associated with hotels
                    branches_result = await conn.execute(text("""
                        SELECT COUNT(*) FROM branches 
                        WHERE hotel_id IS NOT NULL
                    """))
                    branches_with_hotel = branches_result.scalar()
                    
                    total_branches_result = await conn.execute(text("SELECT COUNT(*) FROM branches"))
                    total_branches = total_branches_result.scalar()
                    
                    execution_time = time.time() - start_time
                    
                    if total_branches > 0:
                        if branches_with_hotel == total_branches:
                            results.append(ValidationResult(
                                component="database",
                                test_name="data_segregation_branch_association",
                                status=ValidationStatus.SUCCESS,
                                message="All branches are properly associated with hotels",
                                details={
                                    "total_branches": total_branches,
                                    "branches_with_hotels": branches_with_hotel
                                },
                                execution_time=execution_time
                            ))
                        else:
                            results.append(ValidationResult(
                                component="database",
                                test_name="data_segregation_branch_association",
                                status=ValidationStatus.WARNING,
                                message="Some branches are not associated with hotels",
                                details={
                                    "total_branches": total_branches,
                                    "branches_with_hotels": branches_with_hotel,
                                    "branches_without_hotels": total_branches - branches_with_hotel
                                },
                                suggestions=[
                                    "Review branch creation process",
                                    "Ensure hotel_id is required for branches",
                                    "Check foreign key constraints"
                                ],
                                execution_time=execution_time
                            ))
                    else:
                        results.append(ValidationResult(
                            component="database",
                            test_name="data_segregation_branch_association",
                            status=ValidationStatus.WARNING,
                            message="No branches found to validate data segregation",
                            details={"total_branches": total_branches},
                            suggestions=[
                                "Add test branches to validate data segregation",
                                "Run database seeding scripts"
                            ],
                            execution_time=execution_time
                        ))
                        
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="database",
                    test_name="data_segregation_branch_association",
                    status=ValidationStatus.ERROR,
                    message=f"Error validating branch-based data segregation: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check if branches table exists",
                        "Verify database schema",
                        "Check foreign key constraints"
                    ],
                    execution_time=execution_time
                ))
                
        except Exception as e:
            results.append(ValidationResult(
                component="database",
                test_name="data_segregation",
                status=ValidationStatus.ERROR,
                message=f"Error setting up data segregation validation: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check database connection",
                    "Verify database schema is properly set up"
                ],
                execution_time=0.0
            ))
        
        return results