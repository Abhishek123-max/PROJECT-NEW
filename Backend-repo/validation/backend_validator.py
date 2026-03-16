"""
FastAPI Backend Validator.

Validates FastAPI server health, endpoint functionality, middleware, and error handling.
"""

import asyncio
import time
import httpx
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from .models import ValidationResult, ValidationStatus, APIEndpoint

logger = logging.getLogger(__name__)


class BackendValidator:
    """Validates FastAPI backend functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the backend validator.
        
        Args:
            base_url: Base URL of the FastAPI server
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Define API endpoints to test
        self.endpoints = [
            APIEndpoint(
                method="GET",
                path="/health",
                full_url=f"{self.base_url}/health",
                description="Health check endpoint"
            ),
            APIEndpoint(
                method="GET", 
                path="/ready",
                full_url=f"{self.base_url}/ready",
                description="Readiness check endpoint"
            ),
            APIEndpoint(
                method="GET",
                path="/docs",
                full_url=f"{self.base_url}/docs",
                description="API documentation endpoint"
            ),
            APIEndpoint(
                method="POST",
                path="/api/v1/auth/login",
                full_url=f"{self.base_url}/api/v1/auth/login",
                headers={"Content-Type": "application/json"},
                body={
                    "email": "test@example.com",
                    "password": "testpassword"
                },
                expected_status=401,  # Expect unauthorized for invalid credentials
                description="Login endpoint validation"
            ),
            APIEndpoint(
                method="POST",
                path="/api/v1/auth/refresh",
                full_url=f"{self.base_url}/api/v1/auth/refresh",
                headers={"Content-Type": "application/json"},
                body={"refresh_token": "invalid_token"},
                expected_status=401,  # Expect unauthorized for invalid token
                description="Token refresh endpoint validation"
            ),
            APIEndpoint(
                method="GET",
                path="/api/v1/auth/users/me",
                full_url=f"{self.base_url}/api/v1/auth/users/me",
                headers={"Authorization": "Bearer invalid_token"},
                expected_status=401,  # Expect unauthorized for invalid token
                requires_auth=True,
                description="Protected endpoint validation"
            )
        ]
    
    async def validate_all(self) -> List[ValidationResult]:
        """Run all backend validations.
        
        Returns:
            List of validation results
        """
        results = []
        
        # Check server health
        results.extend(await self.check_server_health())
        
        # Validate endpoints
        results.extend(await self.validate_endpoints())
        
        # Test middleware
        results.extend(await self.test_middleware())
        
        # Verify error handling
        results.extend(await self.verify_error_handling())
        
        await self.client.aclose()
        return results
    
    async def check_server_health(self) -> List[ValidationResult]:
        """Check if FastAPI server is running and healthy.
        
        Returns:
            List of validation results
        """
        results = []
        
        # Test server connectivity
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/health")
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results.append(ValidationResult(
                    component="backend",
                    test_name="server_health_check",
                    status=ValidationStatus.SUCCESS,
                    message="FastAPI server is healthy and responding",
                    details={
                        "status_code": response.status_code,
                        "response": data,
                        "response_time": f"{execution_time:.3f}s"
                    },
                    execution_time=execution_time
                ))
            else:
                results.append(ValidationResult(
                    component="backend",
                    test_name="server_health_check",
                    status=ValidationStatus.ERROR,
                    message=f"Health check failed with status {response.status_code}",
                    details={
                        "status_code": response.status_code,
                        "response": response.text
                    },
                    suggestions=[
                        "Check if the FastAPI server is running",
                        "Verify the server is listening on the correct port",
                        "Check server logs for errors"
                    ],
                    execution_time=execution_time
                ))
                
        except httpx.ConnectError as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="backend",
                test_name="server_health_check",
                status=ValidationStatus.ERROR,
                message="Cannot connect to FastAPI server",
                details={"error": str(e)},
                suggestions=[
                    "Start the FastAPI server using: uvicorn app.main:app --reload",
                    "Check if the server is running on the correct port",
                    "Verify network connectivity",
                    "Check firewall settings"
                ],
                execution_time=execution_time
            ))
        except Exception as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="backend",
                test_name="server_health_check",
                status=ValidationStatus.ERROR,
                message=f"Unexpected error during health check: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                suggestions=[
                    "Check server logs for detailed error information",
                    "Verify server configuration",
                    "Restart the FastAPI server"
                ],
                execution_time=execution_time
            ))
        
        return results
    
    async def validate_endpoints(self) -> List[ValidationResult]:
        """Validate all API endpoints are accessible and return proper responses.
        
        Returns:
            List of validation results
        """
        results = []
        
        for endpoint in self.endpoints:
            start_time = time.time()
            try:
                # Prepare request
                kwargs = {
                    "headers": endpoint.headers,
                    "timeout": 10.0
                }
                
                if endpoint.body:
                    kwargs["json"] = endpoint.body
                
                # Make request
                if endpoint.method.upper() == "GET":
                    response = await self.client.get(endpoint.full_url, **kwargs)
                elif endpoint.method.upper() == "POST":
                    response = await self.client.post(endpoint.full_url, **kwargs)
                elif endpoint.method.upper() == "PUT":
                    response = await self.client.put(endpoint.full_url, **kwargs)
                elif endpoint.method.upper() == "DELETE":
                    response = await self.client.delete(endpoint.full_url, **kwargs)
                else:
                    response = await self.client.request(endpoint.method, endpoint.full_url, **kwargs)
                
                execution_time = time.time() - start_time
                
                # Validate response
                if response.status_code == endpoint.expected_status:
                    results.append(ValidationResult(
                        component="backend",
                        test_name=f"endpoint_{endpoint.method.lower()}_{endpoint.path.replace('/', '_').replace('-', '_')}",
                        status=ValidationStatus.SUCCESS,
                        message=f"Endpoint {endpoint.method} {endpoint.path} is working correctly",
                        details={
                            "method": endpoint.method,
                            "path": endpoint.path,
                            "status_code": response.status_code,
                            "expected_status": endpoint.expected_status,
                            "response_time": f"{execution_time:.3f}s",
                            "description": endpoint.description
                        },
                        execution_time=execution_time
                    ))
                else:
                    results.append(ValidationResult(
                        component="backend",
                        test_name=f"endpoint_{endpoint.method.lower()}_{endpoint.path.replace('/', '_').replace('-', '_')}",
                        status=ValidationStatus.WARNING,
                        message=f"Endpoint {endpoint.method} {endpoint.path} returned unexpected status",
                        details={
                            "method": endpoint.method,
                            "path": endpoint.path,
                            "status_code": response.status_code,
                            "expected_status": endpoint.expected_status,
                            "response": response.text[:500] if response.text else None
                        },
                        suggestions=[
                            "Check endpoint implementation",
                            "Verify request parameters and body",
                            "Review endpoint documentation"
                        ],
                        execution_time=execution_time
                    ))
                    
            except httpx.TimeoutException:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="backend",
                    test_name=f"endpoint_{endpoint.method.lower()}_{endpoint.path.replace('/', '_').replace('-', '_')}",
                    status=ValidationStatus.ERROR,
                    message=f"Endpoint {endpoint.method} {endpoint.path} timed out",
                    details={
                        "method": endpoint.method,
                        "path": endpoint.path,
                        "timeout": "10.0s"
                    },
                    suggestions=[
                        "Check if the endpoint is implemented",
                        "Verify server performance",
                        "Check for blocking operations in the endpoint"
                    ],
                    execution_time=execution_time
                ))
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="backend",
                    test_name=f"endpoint_{endpoint.method.lower()}_{endpoint.path.replace('/', '_').replace('-', '_')}",
                    status=ValidationStatus.ERROR,
                    message=f"Error testing endpoint {endpoint.method} {endpoint.path}: {str(e)}",
                    details={
                        "method": endpoint.method,
                        "path": endpoint.path,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    suggestions=[
                        "Check endpoint implementation",
                        "Verify server is running",
                        "Check server logs for errors"
                    ],
                    execution_time=execution_time
                ))
        
        return results
    
    async def test_middleware(self) -> List[ValidationResult]:
        """Test middleware functionality (CORS, rate limiting, validation).
        
        Returns:
            List of validation results
        """
        results = []
        
        # Test CORS middleware
        start_time = time.time()
        try:
            response = await self.client.options(
                f"{self.base_url}/api/v1/auth/login",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            execution_time = time.time() - start_time
            
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                "access-control-allow-headers": response.headers.get("access-control-allow-headers")
            }
            
            if any(cors_headers.values()):
                results.append(ValidationResult(
                    component="backend",
                    test_name="cors_middleware",
                    status=ValidationStatus.SUCCESS,
                    message="CORS middleware is configured and working",
                    details={
                        "cors_headers": cors_headers,
                        "status_code": response.status_code
                    },
                    execution_time=execution_time
                ))
            else:
                results.append(ValidationResult(
                    component="backend",
                    test_name="cors_middleware",
                    status=ValidationStatus.WARNING,
                    message="CORS headers not found in response",
                    details={
                        "status_code": response.status_code,
                        "headers": dict(response.headers)
                    },
                    suggestions=[
                        "Check CORS middleware configuration",
                        "Verify CORS origins are properly set",
                        "Review FastAPI CORS setup"
                    ],
                    execution_time=execution_time
                ))
                
        except Exception as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="backend",
                test_name="cors_middleware",
                status=ValidationStatus.ERROR,
                message=f"Error testing CORS middleware: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check CORS middleware configuration",
                    "Verify server is running properly"
                ],
                execution_time=execution_time
            ))
        
        # Test request validation middleware
        start_time = time.time()
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"invalid": "data"},  # Invalid request body
                headers={"Content-Type": "application/json"}
            )
            execution_time = time.time() - start_time
            
            if response.status_code == 422:  # Unprocessable Entity
                results.append(ValidationResult(
                    component="backend",
                    test_name="validation_middleware",
                    status=ValidationStatus.SUCCESS,
                    message="Request validation middleware is working correctly",
                    details={
                        "status_code": response.status_code,
                        "validation_response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                    },
                    execution_time=execution_time
                ))
            else:
                results.append(ValidationResult(
                    component="backend",
                    test_name="validation_middleware",
                    status=ValidationStatus.WARNING,
                    message="Request validation may not be working as expected",
                    details={
                        "status_code": response.status_code,
                        "expected_status": 422,
                        "response": response.text[:200]
                    },
                    suggestions=[
                        "Check request validation middleware configuration",
                        "Verify Pydantic models are properly defined",
                        "Review validation error handling"
                    ],
                    execution_time=execution_time
                ))
                
        except Exception as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="backend",
                test_name="validation_middleware",
                status=ValidationStatus.ERROR,
                message=f"Error testing validation middleware: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check validation middleware configuration",
                    "Verify server is running properly"
                ],
                execution_time=execution_time
            ))
        
        return results
    
    async def verify_error_handling(self) -> List[ValidationResult]:
        """Verify error handling is working as expected.
        
        Returns:
            List of validation results
        """
        results = []
        
        # Test 404 error handling
        start_time = time.time()
        try:
            response = await self.client.get(f"{self.base_url}/nonexistent-endpoint")
            execution_time = time.time() - start_time
            
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    if "error_code" in error_data or "message" in error_data:
                        results.append(ValidationResult(
                            component="backend",
                            test_name="error_handling_404",
                            status=ValidationStatus.SUCCESS,
                            message="404 error handling is working correctly",
                            details={
                                "status_code": response.status_code,
                                "error_response": error_data
                            },
                            execution_time=execution_time
                        ))
                    else:
                        results.append(ValidationResult(
                            component="backend",
                            test_name="error_handling_404",
                            status=ValidationStatus.WARNING,
                            message="404 error response format could be improved",
                            details={
                                "status_code": response.status_code,
                                "response": error_data
                            },
                            suggestions=[
                                "Ensure error responses include error_code and message fields",
                                "Review error response format consistency"
                            ],
                            execution_time=execution_time
                        ))
                except:
                    results.append(ValidationResult(
                        component="backend",
                        test_name="error_handling_404",
                        status=ValidationStatus.WARNING,
                        message="404 error response is not in JSON format",
                        details={
                            "status_code": response.status_code,
                            "response": response.text[:200]
                        },
                        suggestions=[
                            "Consider returning JSON error responses",
                            "Review error handling middleware"
                        ],
                        execution_time=execution_time
                    ))
            else:
                results.append(ValidationResult(
                    component="backend",
                    test_name="error_handling_404",
                    status=ValidationStatus.ERROR,
                    message=f"Expected 404 status code, got {response.status_code}",
                    details={
                        "status_code": response.status_code,
                        "expected_status": 404
                    },
                    suggestions=[
                        "Check FastAPI routing configuration",
                        "Verify 404 error handling is implemented"
                    ],
                    execution_time=execution_time
                ))
                
        except Exception as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="backend",
                test_name="error_handling_404",
                status=ValidationStatus.ERROR,
                message=f"Error testing 404 handling: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check error handling configuration",
                    "Verify server is running properly"
                ],
                execution_time=execution_time
            ))
        
        return results