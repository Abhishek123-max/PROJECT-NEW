"""
Main System Validator.

Orchestrates comprehensive validation of FastAPI backend, Redis, and PostgreSQL components.
"""

import asyncio
import time
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import ValidationResult, ValidationStatus, ValidationSummary
from .backend_validator import BackendValidator
from .redis_validator import RedisValidator
from .database_validator import DatabaseValidator

logger = logging.getLogger(__name__)


class SystemValidator:
    """Main system validator that orchestrates all validation components."""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 redis_url: str = "redis://localhost:6379/0",
                 database_url: str = None):
        """Initialize the system validator.
        
        Args:
            base_url: FastAPI server base URL
            redis_url: Redis connection URL
            database_url: PostgreSQL connection URL
        """
        self.base_url = base_url
        self.redis_url = redis_url
        self.database_url = database_url
        
        # Initialize validators
        self.backend_validator = BackendValidator(base_url)
        self.redis_validator = RedisValidator(redis_url)
        self.database_validator = DatabaseValidator(database_url) if database_url else None
        
        # Validation summary
        self.summary = ValidationSummary()
    
    async def run_full_validation(self, 
                                 include_backend: bool = True,
                                 include_redis: bool = True,
                                 include_database: bool = True,
                                 parallel: bool = True) -> ValidationSummary:
        """Run comprehensive validation of all system components.
        
        Args:
            include_backend: Whether to validate FastAPI backend
            include_redis: Whether to validate Redis
            include_database: Whether to validate database
            parallel: Whether to run validations in parallel
            
        Returns:
            ValidationSummary with all results
        """
        logger.info("Starting comprehensive system validation...")
        start_time = time.time()
        
        # Reset summary
        self.summary = ValidationSummary()
        
        try:
            if parallel:
                # Run validations in parallel
                tasks = []
                
                if include_backend:
                    tasks.append(self._run_backend_validation())
                
                if include_redis:
                    tasks.append(self._run_redis_validation())
                
                if include_database and self.database_validator:
                    tasks.append(self._run_database_validation())
                
                if tasks:
                    results_lists = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for results in results_lists:
                        if isinstance(results, Exception):
                            # Handle exceptions from parallel execution
                            self.summary.add_result(ValidationResult(
                                component="system",
                                test_name="parallel_execution_error",
                                status=ValidationStatus.ERROR,
                                message=f"Error during parallel validation: {str(results)}",
                                details={"error": str(results), "error_type": type(results).__name__},
                                suggestions=[
                                    "Check system resources",
                                    "Try running validations sequentially",
                                    "Check individual component configurations"
                                ]
                            ))
                        else:
                            for result in results:
                                self.summary.add_result(result)
            else:
                # Run validations sequentially
                if include_backend:
                    backend_results = await self._run_backend_validation()
                    for result in backend_results:
                        self.summary.add_result(result)
                
                if include_redis:
                    redis_results = await self._run_redis_validation()
                    for result in redis_results:
                        self.summary.add_result(result)
                
                if include_database and self.database_validator:
                    database_results = await self._run_database_validation()
                    for result in database_results:
                        self.summary.add_result(result)
            
            # Calculate total execution time
            total_time = time.time() - start_time
            self.summary.execution_time = total_time
            
            # Log summary
            logger.info(f"Validation completed in {total_time:.2f}s")
            logger.info(f"Results: {self.summary.passed} passed, {self.summary.warnings} warnings, {self.summary.errors} errors")
            
            return self.summary
            
        except Exception as e:
            logger.error(f"Unexpected error during system validation: {str(e)}")
            self.summary.add_result(ValidationResult(
                component="system",
                test_name="system_validation_error",
                status=ValidationStatus.ERROR,
                message=f"Unexpected system validation error: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                suggestions=[
                    "Check system configuration",
                    "Verify all services are accessible",
                    "Check system logs for more details"
                ]
            ))
            return self.summary
    
    async def _run_backend_validation(self) -> List[ValidationResult]:
        """Run backend validation with error handling."""
        try:
            logger.info("Running FastAPI backend validation...")
            return await self.backend_validator.validate_all()
        except Exception as e:
            logger.error(f"Backend validation failed: {str(e)}")
            return [ValidationResult(
                component="backend",
                test_name="backend_validation_error",
                status=ValidationStatus.ERROR,
                message=f"Backend validation failed: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check if FastAPI server is running",
                    "Verify backend configuration",
                    "Check server logs for errors"
                ]
            )]
    
    async def _run_redis_validation(self) -> List[ValidationResult]:
        """Run Redis validation with error handling."""
        try:
            logger.info("Running Redis validation...")
            return await self.redis_validator.validate_all()
        except Exception as e:
            logger.error(f"Redis validation failed: {str(e)}")
            return [ValidationResult(
                component="redis",
                test_name="redis_validation_error",
                status=ValidationStatus.ERROR,
                message=f"Redis validation failed: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check if Redis server is running",
                    "Verify Redis configuration",
                    "Check Redis server logs"
                ]
            )]
    
    async def _run_database_validation(self) -> List[ValidationResult]:
        """Run database validation with error handling."""
        try:
            logger.info("Running database validation...")
            return await self.database_validator.validate_all()
        except Exception as e:
            logger.error(f"Database validation failed: {str(e)}")
            return [ValidationResult(
                component="database",
                test_name="database_validation_error",
                status=ValidationStatus.ERROR,
                message=f"Database validation failed: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check if PostgreSQL server is running",
                    "Verify database configuration",
                    "Check database server logs"
                ]
            )]
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive validation report.
        
        Args:
            output_file: Optional file path to save the report
            
        Returns:
            Dictionary containing the full report
        """
        report = {
            "validation_report": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "summary": self.summary.to_dict(),
                "components": self._generate_component_reports(),
                "recommendations": self._generate_recommendations(),
                "system_health": self._assess_system_health()
            }
        }
        
        if output_file:
            try:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Validation report saved to: {output_path}")
            except Exception as e:
                logger.error(f"Failed to save report to {output_file}: {str(e)}")
        
        return report
    
    def _generate_component_reports(self) -> Dict[str, Any]:
        """Generate detailed reports for each component."""
        components = {}
        
        for component in ["backend", "redis", "database"]:
            component_results = [r for r in self.summary.results if r.component == component]
            
            if component_results:
                components[component] = {
                    "total_tests": len(component_results),
                    "passed": len([r for r in component_results if r.status == ValidationStatus.SUCCESS]),
                    "warnings": len([r for r in component_results if r.status == ValidationStatus.WARNING]),
                    "errors": len([r for r in component_results if r.status == ValidationStatus.ERROR]),
                    "execution_time": sum(r.execution_time for r in component_results),
                    "tests": [r.to_dict() for r in component_results]
                }
        
        return components
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Collect all suggestions from failed tests
        error_suggestions = []
        warning_suggestions = []
        
        for result in self.summary.results:
            if result.status == ValidationStatus.ERROR and result.suggestions:
                error_suggestions.extend(result.suggestions)
            elif result.status == ValidationStatus.WARNING and result.suggestions:
                warning_suggestions.extend(result.suggestions)
        
        # Remove duplicates while preserving order
        unique_error_suggestions = list(dict.fromkeys(error_suggestions))
        unique_warning_suggestions = list(dict.fromkeys(warning_suggestions))
        
        if unique_error_suggestions:
            recommendations.append({
                "priority": "high",
                "category": "critical_issues",
                "title": "Critical Issues Requiring Immediate Attention",
                "suggestions": unique_error_suggestions
            })
        
        if unique_warning_suggestions:
            recommendations.append({
                "priority": "medium",
                "category": "improvements",
                "title": "Recommended Improvements",
                "suggestions": unique_warning_suggestions
            })
        
        # Add general recommendations based on overall health
        if self.summary.success_rate < 50:
            recommendations.append({
                "priority": "high",
                "category": "system_health",
                "title": "System Health Critical",
                "suggestions": [
                    "Review system configuration and setup",
                    "Check all service dependencies",
                    "Consider running individual component validations",
                    "Review system logs for detailed error information"
                ]
            })
        elif self.summary.success_rate < 80:
            recommendations.append({
                "priority": "medium",
                "category": "system_health",
                "title": "System Health Needs Attention",
                "suggestions": [
                    "Address warning conditions to improve stability",
                    "Review component configurations",
                    "Consider performance optimizations"
                ]
            })
        
        return recommendations
    
    def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health based on validation results."""
        health_status = "healthy"
        health_score = self.summary.success_rate
        
        if self.summary.errors > 0:
            if self.summary.success_rate < 50:
                health_status = "critical"
            elif self.summary.success_rate < 80:
                health_status = "degraded"
            else:
                health_status = "warning"
        elif self.summary.warnings > 0:
            health_status = "warning"
        
        return {
            "status": health_status,
            "score": round(health_score, 2),
            "description": self._get_health_description(health_status, health_score),
            "components_status": self._get_components_health()
        }
    
    def _get_health_description(self, status: str, score: float) -> str:
        """Get health description based on status and score."""
        descriptions = {
            "healthy": f"System is operating normally with {score:.1f}% success rate",
            "warning": f"System is functional but has some issues ({score:.1f}% success rate)",
            "degraded": f"System has significant issues affecting functionality ({score:.1f}% success rate)",
            "critical": f"System has critical issues requiring immediate attention ({score:.1f}% success rate)"
        }
        return descriptions.get(status, f"System status unknown ({score:.1f}% success rate)")
    
    def _get_components_health(self) -> Dict[str, str]:
        """Get health status for each component."""
        components_health = {}
        
        for component in ["backend", "redis", "database"]:
            component_results = [r for r in self.summary.results if r.component == component]
            
            if not component_results:
                components_health[component] = "not_tested"
                continue
            
            errors = len([r for r in component_results if r.status == ValidationStatus.ERROR])
            warnings = len([r for r in component_results if r.status == ValidationStatus.WARNING])
            
            if errors > 0:
                components_health[component] = "error"
            elif warnings > 0:
                components_health[component] = "warning"
            else:
                components_health[component] = "healthy"
        
        return components_health
    
    def print_summary(self):
        """Print a formatted summary of validation results."""
        print("\n" + "="*80)
        print("SYSTEM VALIDATION SUMMARY")
        print("="*80)
        
        print(f"Total Tests: {self.summary.total_tests}")
        print(f"Passed: {self.summary.passed}")
        print(f"Warnings: {self.summary.warnings}")
        print(f"Errors: {self.summary.errors}")
        print(f"Success Rate: {self.summary.success_rate:.1f}%")
        print(f"Execution Time: {self.summary.execution_time:.2f}s")
        
        # Component breakdown
        print("\nCOMPONENT BREAKDOWN:")
        print("-" * 40)
        
        for component in ["backend", "redis", "database"]:
            component_results = [r for r in self.summary.results if r.component == component]
            if component_results:
                passed = len([r for r in component_results if r.status == ValidationStatus.SUCCESS])
                warnings = len([r for r in component_results if r.status == ValidationStatus.WARNING])
                errors = len([r for r in component_results if r.status == ValidationStatus.ERROR])
                
                print(f"{component.upper()}: {passed} passed, {warnings} warnings, {errors} errors")
        
        # Show errors and warnings
        if self.summary.errors > 0:
            print("\nERRORS:")
            print("-" * 40)
            for result in self.summary.results:
                if result.status == ValidationStatus.ERROR:
                    print(f"❌ {result.component}.{result.test_name}: {result.message}")
        
        if self.summary.warnings > 0:
            print("\nWARNINGS:")
            print("-" * 40)
            for result in self.summary.results:
                if result.status == ValidationStatus.WARNING:
                    print(f"⚠️  {result.component}.{result.test_name}: {result.message}")
        
        print("\n" + "="*80)