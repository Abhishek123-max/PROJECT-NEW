"""
Data models for the validation system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional


class ValidationStatus(Enum):
    """Validation status enumeration."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    component: str
    test_name: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    suggestions: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "component": self.component,
            "test_name": self.test_name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "suggestions": self.suggestions,
            "execution_time": self.execution_time
        }


@dataclass
class ValidationSummary:
    """Summary of all validation results."""
    total_tests: int = 0
    passed: int = 0
    warnings: int = 0
    errors: int = 0
    skipped: int = 0
    execution_time: float = 0.0
    results: List[ValidationResult] = field(default_factory=list)
    
    def add_result(self, result: ValidationResult):
        """Add a validation result to the summary."""
        self.results.append(result)
        self.total_tests += 1
        self.execution_time += result.execution_time
        
        if result.status == ValidationStatus.SUCCESS:
            self.passed += 1
        elif result.status == ValidationStatus.WARNING:
            self.warnings += 1
        elif result.status == ValidationStatus.ERROR:
            self.errors += 1
        elif result.status == ValidationStatus.SKIPPED:
            self.skipped += 1
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return self.errors > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return self.warnings > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
            "skipped": self.skipped,
            "success_rate": round(self.success_rate, 2),
            "execution_time": round(self.execution_time, 2),
            "results": [result.to_dict() for result in self.results]
        }


@dataclass
class APIEndpoint:
    """API endpoint information for testing."""
    method: str
    path: str
    full_url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    requires_auth: bool = False
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "method": self.method,
            "path": self.path,
            "full_url": self.full_url,
            "headers": self.headers,
            "body": self.body,
            "expected_status": self.expected_status,
            "requires_auth": self.requires_auth,
            "description": self.description
        }


@dataclass
class DatabaseTable:
    """Database table information for validation."""
    name: str
    required_columns: List[str] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "required_columns": self.required_columns,
            "indexes": self.indexes,
            "constraints": self.constraints,
            "description": self.description
        }