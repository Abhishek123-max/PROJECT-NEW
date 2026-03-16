"""
Redis Validator.

Validates Redis connectivity, CRUD operations, rate limiting, and session management.
"""

import asyncio
import time
import json
import logging
from typing import List, Dict, Any, Optional
try:
    import redis.asyncio as redis
    from redis.exceptions import ConnectionError, TimeoutError, RedisError
except ImportError:
    # Fallback for older Redis versions
    import redis
    from redis.exceptions import ConnectionError, TimeoutError, RedisError

from .models import ValidationResult, ValidationStatus

logger = logging.getLogger(__name__)


class RedisValidator:
    """Validates Redis functionality."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize the Redis validator.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        
    async def _get_redis_client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                max_connections=10
            )
        return self.redis_client
    
    async def validate_all(self) -> List[ValidationResult]:
        """Run all Redis validations.
        
        Returns:
            List of validation results
        """
        results = []
        
        try:
            # Test connection
            results.extend(await self.test_connection())
            
            # Test CRUD operations
            results.extend(await self.test_crud_operations())
            
            # Test rate limiting functionality
            results.extend(await self.validate_rate_limiting())
            
            # Test session management
            results.extend(await self.test_session_management())
            
        finally:
            # Clean up
            if self.redis_client:
                await self.redis_client.aclose()
        
        return results
    
    async def test_connection(self) -> List[ValidationResult]:
        """Test Redis server connection.
        
        Returns:
            List of validation results
        """
        results = []
        
        start_time = time.time()
        try:
            client = await self._get_redis_client()
            
            # Test basic ping
            pong = await client.ping()
            execution_time = time.time() - start_time
            
            if pong:
                # Get Redis info
                info = await client.info()
                
                results.append(ValidationResult(
                    component="redis",
                    test_name="connection_test",
                    status=ValidationStatus.SUCCESS,
                    message="Redis connection is working correctly",
                    details={
                        "ping_response": pong,
                        "redis_version": info.get("redis_version"),
                        "connected_clients": info.get("connected_clients"),
                        "used_memory_human": info.get("used_memory_human"),
                        "response_time": f"{execution_time:.3f}s"
                    },
                    execution_time=execution_time
                ))
            else:
                results.append(ValidationResult(
                    component="redis",
                    test_name="connection_test",
                    status=ValidationStatus.ERROR,
                    message="Redis ping failed",
                    details={"ping_response": pong},
                    suggestions=[
                        "Check if Redis server is running",
                        "Verify Redis connection URL",
                        "Check network connectivity"
                    ],
                    execution_time=execution_time
                ))
                
        except ConnectionError as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="redis",
                test_name="connection_test",
                status=ValidationStatus.ERROR,
                message="Cannot connect to Redis server",
                details={"error": str(e)},
                suggestions=[
                    "Start Redis server: redis-server",
                    "Check if Redis is running on the correct port",
                    "Verify Redis connection URL in configuration",
                    "Check firewall settings"
                ],
                execution_time=execution_time
            ))
        except TimeoutError as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="redis",
                test_name="connection_test",
                status=ValidationStatus.ERROR,
                message="Redis connection timed out",
                details={"error": str(e)},
                suggestions=[
                    "Check Redis server performance",
                    "Verify network connectivity",
                    "Increase connection timeout if needed"
                ],
                execution_time=execution_time
            ))
        except Exception as e:
            execution_time = time.time() - start_time
            results.append(ValidationResult(
                component="redis",
                test_name="connection_test",
                status=ValidationStatus.ERROR,
                message=f"Unexpected error connecting to Redis: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                suggestions=[
                    "Check Redis server configuration",
                    "Verify Redis connection parameters",
                    "Check Redis server logs"
                ],
                execution_time=execution_time
            ))
        
        return results
    
    async def test_crud_operations(self) -> List[ValidationResult]:
        """Test Redis CRUD operations (SET, GET, DEL).
        
        Returns:
            List of validation results
        """
        results = []
        
        try:
            client = await self._get_redis_client()
            test_key = "validation_test_key"
            test_value = "validation_test_value"
            
            # Test SET operation
            start_time = time.time()
            try:
                set_result = await client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
                execution_time = time.time() - start_time
                
                if set_result:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="crud_set_operation",
                        status=ValidationStatus.SUCCESS,
                        message="Redis SET operation is working correctly",
                        details={
                            "key": test_key,
                            "value": test_value,
                            "set_result": set_result,
                            "expiration": "60 seconds"
                        },
                        execution_time=execution_time
                    ))
                else:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="crud_set_operation",
                        status=ValidationStatus.ERROR,
                        message="Redis SET operation failed",
                        details={"set_result": set_result},
                        suggestions=[
                            "Check Redis server status",
                            "Verify Redis permissions",
                            "Check available memory"
                        ],
                        execution_time=execution_time
                    ))
                    
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="redis",
                    test_name="crud_set_operation",
                    status=ValidationStatus.ERROR,
                    message=f"Error during SET operation: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check Redis server status",
                        "Verify Redis connection"
                    ],
                    execution_time=execution_time
                ))
            
            # Test GET operation
            start_time = time.time()
            try:
                get_result = await client.get(test_key)
                execution_time = time.time() - start_time
                
                if get_result == test_value:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="crud_get_operation",
                        status=ValidationStatus.SUCCESS,
                        message="Redis GET operation is working correctly",
                        details={
                            "key": test_key,
                            "expected_value": test_value,
                            "actual_value": get_result
                        },
                        execution_time=execution_time
                    ))
                else:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="crud_get_operation",
                        status=ValidationStatus.ERROR,
                        message="Redis GET operation returned unexpected value",
                        details={
                            "key": test_key,
                            "expected_value": test_value,
                            "actual_value": get_result
                        },
                        suggestions=[
                            "Check Redis data integrity",
                            "Verify SET operation succeeded"
                        ],
                        execution_time=execution_time
                    ))
                    
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="redis",
                    test_name="crud_get_operation",
                    status=ValidationStatus.ERROR,
                    message=f"Error during GET operation: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check Redis server status",
                        "Verify Redis connection"
                    ],
                    execution_time=execution_time
                ))
            
            # Test DEL operation
            start_time = time.time()
            try:
                del_result = await client.delete(test_key)
                execution_time = time.time() - start_time
                
                if del_result > 0:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="crud_del_operation",
                        status=ValidationStatus.SUCCESS,
                        message="Redis DEL operation is working correctly",
                        details={
                            "key": test_key,
                            "deleted_count": del_result
                        },
                        execution_time=execution_time
                    ))
                else:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="crud_del_operation",
                        status=ValidationStatus.WARNING,
                        message="Redis DEL operation did not delete any keys",
                        details={
                            "key": test_key,
                            "deleted_count": del_result
                        },
                        suggestions=[
                            "Verify the key exists before deletion",
                            "Check if key was already expired"
                        ],
                        execution_time=execution_time
                    ))
                    
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="redis",
                    test_name="crud_del_operation",
                    status=ValidationStatus.ERROR,
                    message=f"Error during DEL operation: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check Redis server status",
                        "Verify Redis connection"
                    ],
                    execution_time=execution_time
                ))
            
        except Exception as e:
            results.append(ValidationResult(
                component="redis",
                test_name="crud_operations",
                status=ValidationStatus.ERROR,
                message=f"Error setting up CRUD operations test: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check Redis connection",
                    "Verify Redis server is running"
                ],
                execution_time=0.0
            ))
        
        return results
    
    async def validate_rate_limiting(self) -> List[ValidationResult]:
        """Test rate limiting functionality using Redis.
        
        Returns:
            List of validation results
        """
        results = []
        
        try:
            client = await self._get_redis_client()
            rate_limit_key = "rate_limit_test:127.0.0.1"
            
            # Test rate limiting counter
            start_time = time.time()
            try:
                # Simulate rate limiting by incrementing a counter
                pipe = client.pipeline()
                pipe.incr(rate_limit_key)
                pipe.expire(rate_limit_key, 60)  # 60 second window
                results_pipe = await pipe.execute()
                
                execution_time = time.time() - start_time
                
                if results_pipe and len(results_pipe) >= 2:
                    count = results_pipe[0]
                    expire_set = results_pipe[1]
                    
                    results.append(ValidationResult(
                        component="redis",
                        test_name="rate_limiting_counter",
                        status=ValidationStatus.SUCCESS,
                        message="Redis rate limiting counter is working correctly",
                        details={
                            "key": rate_limit_key,
                            "count": count,
                            "expire_set": expire_set,
                            "window": "60 seconds"
                        },
                        execution_time=execution_time
                    ))
                else:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="rate_limiting_counter",
                        status=ValidationStatus.ERROR,
                        message="Redis rate limiting pipeline failed",
                        details={"pipeline_results": results_pipe},
                        suggestions=[
                            "Check Redis pipeline functionality",
                            "Verify Redis server status"
                        ],
                        execution_time=execution_time
                    ))
                    
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="redis",
                    test_name="rate_limiting_counter",
                    status=ValidationStatus.ERROR,
                    message=f"Error testing rate limiting: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check Redis server status",
                        "Verify Redis pipeline support"
                    ],
                    execution_time=execution_time
                ))
            
            # Clean up test key
            try:
                await client.delete(rate_limit_key)
            except:
                pass  # Ignore cleanup errors
                
        except Exception as e:
            results.append(ValidationResult(
                component="redis",
                test_name="rate_limiting",
                status=ValidationStatus.ERROR,
                message=f"Error setting up rate limiting test: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check Redis connection",
                    "Verify Redis server is running"
                ],
                execution_time=0.0
            ))
        
        return results
    
    async def test_session_management(self) -> List[ValidationResult]:
        """Test session storage and retrieval functionality.
        
        Returns:
            List of validation results
        """
        results = []
        
        try:
            client = await self._get_redis_client()
            session_key = "session:test_user_123"
            session_data = {
                "user_id": 123,
                "email": "test@example.com",
                "role": "user",
                "hotel_id": 1,
                "created_at": "2025-01-09T10:30:00Z"
            }
            
            # Test session storage
            start_time = time.time()
            try:
                session_json = json.dumps(session_data)
                set_result = await client.setex(session_key, 3600, session_json)  # 1 hour expiration
                execution_time = time.time() - start_time
                
                if set_result:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="session_storage",
                        status=ValidationStatus.SUCCESS,
                        message="Redis session storage is working correctly",
                        details={
                            "session_key": session_key,
                            "session_data": session_data,
                            "expiration": "3600 seconds"
                        },
                        execution_time=execution_time
                    ))
                else:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="session_storage",
                        status=ValidationStatus.ERROR,
                        message="Redis session storage failed",
                        details={"set_result": set_result},
                        suggestions=[
                            "Check Redis server status",
                            "Verify Redis memory availability"
                        ],
                        execution_time=execution_time
                    ))
                    
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="redis",
                    test_name="session_storage",
                    status=ValidationStatus.ERROR,
                    message=f"Error storing session: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check Redis server status",
                        "Verify JSON serialization"
                    ],
                    execution_time=execution_time
                ))
            
            # Test session retrieval
            start_time = time.time()
            try:
                retrieved_json = await client.get(session_key)
                execution_time = time.time() - start_time
                
                if retrieved_json:
                    retrieved_data = json.loads(retrieved_json)
                    
                    if retrieved_data == session_data:
                        results.append(ValidationResult(
                            component="redis",
                            test_name="session_retrieval",
                            status=ValidationStatus.SUCCESS,
                            message="Redis session retrieval is working correctly",
                            details={
                                "session_key": session_key,
                                "retrieved_data": retrieved_data
                            },
                            execution_time=execution_time
                        ))
                    else:
                        results.append(ValidationResult(
                            component="redis",
                            test_name="session_retrieval",
                            status=ValidationStatus.ERROR,
                            message="Retrieved session data does not match stored data",
                            details={
                                "expected": session_data,
                                "retrieved": retrieved_data
                            },
                            suggestions=[
                                "Check JSON serialization/deserialization",
                                "Verify Redis data integrity"
                            ],
                            execution_time=execution_time
                        ))
                else:
                    results.append(ValidationResult(
                        component="redis",
                        test_name="session_retrieval",
                        status=ValidationStatus.ERROR,
                        message="Session data not found in Redis",
                        details={"session_key": session_key},
                        suggestions=[
                            "Verify session was stored successfully",
                            "Check if session expired"
                        ],
                        execution_time=execution_time
                    ))
                    
            except json.JSONDecodeError as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="redis",
                    test_name="session_retrieval",
                    status=ValidationStatus.ERROR,
                    message="Error parsing retrieved session JSON",
                    details={"error": str(e), "raw_data": retrieved_json},
                    suggestions=[
                        "Check JSON format in stored session",
                        "Verify data serialization process"
                    ],
                    execution_time=execution_time
                ))
            except Exception as e:
                execution_time = time.time() - start_time
                results.append(ValidationResult(
                    component="redis",
                    test_name="session_retrieval",
                    status=ValidationStatus.ERROR,
                    message=f"Error retrieving session: {str(e)}",
                    details={"error": str(e)},
                    suggestions=[
                        "Check Redis server status",
                        "Verify Redis connection"
                    ],
                    execution_time=execution_time
                ))
            
            # Clean up test session
            try:
                await client.delete(session_key)
            except:
                pass  # Ignore cleanup errors
                
        except Exception as e:
            results.append(ValidationResult(
                component="redis",
                test_name="session_management",
                status=ValidationStatus.ERROR,
                message=f"Error setting up session management test: {str(e)}",
                details={"error": str(e)},
                suggestions=[
                    "Check Redis connection",
                    "Verify Redis server is running"
                ],
                execution_time=0.0
            ))
        
        return results