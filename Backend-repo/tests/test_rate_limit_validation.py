"""
Tests for rate limiting and request validation middleware.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import Response

from ..app.middleware.rate_limit import RateLimitMiddleware, BruteForceProtection
from ..app.middleware.validation import RequestValidationMiddleware, InputSanitizer


class TestRateLimitMiddleware:
    """Test rate limiting middleware functionality."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = Mock()
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        redis_mock.exists.return_value = False
        redis_mock.pipeline.return_value = redis_mock
        redis_mock.incr.return_value = 1
        redis_mock.expire.return_value = True
        redis_mock.execute.return_value = [1, True]
        return redis_mock
    
    @pytest.fixture
    def rate_limit_middleware(self, mock_redis):
        """Create rate limit middleware with mocked Redis."""
        app = FastAPI()
        return RateLimitMiddleware(app, redis_client=mock_redis)
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.path = "/auth/login"
        request.headers = {"User-Agent": "TestClient/1.0"}
        return request
    
    def test_get_client_ip_forwarded(self, rate_limit_middleware):
        """Test IP extraction with forwarded headers."""
        request = Mock(spec=Request)
        request.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = rate_limit_middleware._get_client_ip(request)
        assert ip == "203.0.113.1"
    
    def test_get_client_ip_real_ip(self, rate_limit_middleware):
        """Test IP extraction with X-Real-IP header."""
        request = Mock(spec=Request)
        request.headers = {"X-Real-IP": "203.0.113.2"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = rate_limit_middleware._get_client_ip(request)
        assert ip == "203.0.113.2"
    
    def test_get_client_ip_direct(self, rate_limit_middleware):
        """Test IP extraction from direct client."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = rate_limit_middleware._get_client_ip(request)
        assert ip == "192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_check_general_rate_limit_under_limit(self, rate_limit_middleware, mock_redis):
        """Test general rate limiting under limit."""
        mock_redis.get.return_value = "50"  # Under limit of 100
        
        # Should not raise exception
        await rate_limit_middleware._check_general_rate_limit("192.168.1.1", "/api/test")
        
        # Should increment counter
        mock_redis.pipeline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_auth_rate_limit_over_limit(self, rate_limit_middleware, mock_redis):
        """Test auth rate limiting over limit."""
        mock_redis.get.return_value = "6"  # Over limit of 5
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await rate_limit_middleware._check_auth_rate_limit("192.168.1.1", "/auth/login")
    
    @pytest.mark.asyncio
    async def test_record_failed_attempt(self, rate_limit_middleware, mock_redis):
        """Test recording failed attempts."""
        mock_redis.get.return_value = None
        
        await rate_limit_middleware._record_failed_attempt("192.168.1.1", "login_failure")
        
        # Should store attempt data
        mock_redis.setex.assert_called()
        args = mock_redis.setex.call_args[0]
        assert args[0] == "failed_attempts:192.168.1.1"
        assert args[1] == 86400  # 24 hours
        
        # Verify JSON data structure
        stored_data = json.loads(args[2])
        assert len(stored_data) == 1
        assert stored_data[0]["type"] == "login_failure"
        assert "timestamp" in stored_data[0]


class TestBruteForceProtection:
    """Test brute force protection functionality."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = Mock()
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        return redis_mock
    
    @pytest.fixture
    def brute_force_protection(self, mock_redis):
        """Create brute force protection with mocked Redis."""
        return BruteForceProtection(redis_client=mock_redis)
    
    @pytest.mark.asyncio
    async def test_record_login_attempt_success(self, brute_force_protection, mock_redis):
        """Test recording successful login attempt."""
        await brute_force_protection.record_login_attempt(
            identifier="test@example.com",
            success=True,
            ip_address="192.168.1.1",
            user_agent="TestClient/1.0"
        )
        
        # Should record for both user and IP
        assert mock_redis.setex.call_count == 2
        
        # Check user key
        user_call = mock_redis.setex.call_args_list[0]
        assert user_call[0][0] == "login_attempts:user:test@example.com"
        
        # Check IP key
        ip_call = mock_redis.setex.call_args_list[1]
        assert ip_call[0][0] == "login_attempts:ip:192.168.1.1"
    
    @pytest.mark.asyncio
    async def test_record_login_attempt_failure(self, brute_force_protection, mock_redis):
        """Test recording failed login attempt."""
        await brute_force_protection.record_login_attempt(
            identifier="test@example.com",
            success=False,
            ip_address="192.168.1.1",
            user_agent="TestClient/1.0"
        )
        
        # Should record for both user and IP
        assert mock_redis.setex.call_count == 2
        
        # Verify failure is recorded
        user_call = mock_redis.setex.call_args_list[0]
        stored_data = json.loads(user_call[0][2])
        assert stored_data[0]["success"] is False
    
    @pytest.mark.asyncio
    async def test_is_blocked_not_blocked(self, brute_force_protection, mock_redis):
        """Test checking block status when not blocked."""
        mock_redis.get.return_value = None
        
        result = await brute_force_protection.is_blocked("test@example.com", "192.168.1.1")
        
        assert result["blocked"] is False
    
    @pytest.mark.asyncio
    async def test_is_blocked_user_blocked(self, brute_force_protection, mock_redis):
        """Test checking block status when user is blocked."""
        # Mock recent failed attempts
        from datetime import datetime, timedelta
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        
        failed_attempts = [
            {"timestamp": recent_time.isoformat(), "success": False, "additional_info": "192.168.1.1", "user_agent": "TestClient/1.0"}
            for _ in range(6)  # 6 failed attempts (over limit of 5)
        ]
        
        def mock_get(key):
            if "user:" in key:
                return json.dumps(failed_attempts)
            return None
        
        mock_redis.get.side_effect = mock_get
        
        result = await brute_force_protection.is_blocked("test@example.com", "192.168.1.1")
        
        assert result["blocked"] is True
        assert result["user_blocked"] is True
        assert result["retry_after"] == 900  # 15 minutes


class TestRequestValidationMiddleware:
    """Test request validation middleware functionality."""
    
    @pytest.fixture
    def validation_middleware(self):
        """Create validation middleware."""
        app = FastAPI()
        return RequestValidationMiddleware(app)
    
    def test_contains_malicious_content_sql_injection(self, validation_middleware):
        """Test SQL injection detection."""
        malicious_content = "'; DROP TABLE users; --"
        assert validation_middleware._contains_malicious_content(malicious_content) is True
    
    def test_contains_malicious_content_xss(self, validation_middleware):
        """Test XSS detection."""
        malicious_content = "<script>alert('xss')</script>"
        assert validation_middleware._contains_malicious_content(malicious_content) is True
    
    def test_contains_malicious_content_clean(self, validation_middleware):
        """Test clean content."""
        clean_content = "This is a normal string with no malicious content"
        assert validation_middleware._contains_malicious_content(clean_content) is False
    
    def test_get_json_depth_simple(self, validation_middleware):
        """Test JSON depth calculation for simple object."""
        simple_json = {"key": "value"}
        depth = validation_middleware._get_json_depth(simple_json)
        assert depth == 0
    
    def test_get_json_depth_nested(self, validation_middleware):
        """Test JSON depth calculation for nested object."""
        nested_json = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        depth = validation_middleware._get_json_depth(nested_json)
        assert depth == 3
    
    def test_is_valid_email_valid(self, validation_middleware):
        """Test valid email validation."""
        valid_email = "test@example.com"
        assert validation_middleware._is_valid_email(valid_email) is True
    
    def test_is_valid_email_invalid(self, validation_middleware):
        """Test invalid email validation."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            ""
        ]
        
        for email in invalid_emails:
            assert validation_middleware._is_valid_email(email) is False


class TestInputSanitizer:
    """Test input sanitization functionality."""
    
    def test_sanitize_string_normal(self):
        """Test normal string sanitization."""
        input_str = "Normal string"
        result = InputSanitizer.sanitize_string(input_str)
        assert result == "Normal string"
    
    def test_sanitize_string_with_null_bytes(self):
        """Test string sanitization with null bytes."""
        input_str = "String with\x00null byte"
        result = InputSanitizer.sanitize_string(input_str)
        assert result == "String withnull byte"
    
    def test_sanitize_string_with_control_chars(self):
        """Test string sanitization with control characters."""
        input_str = "String with\x01control\x02chars"
        result = InputSanitizer.sanitize_string(input_str)
        assert result == "String withcontrolchars"
    
    def test_sanitize_string_max_length(self):
        """Test string sanitization with max length."""
        input_str = "A" * 300
        result = InputSanitizer.sanitize_string(input_str, max_length=100)
        assert len(result) == 100
        assert result == "A" * 100
    
    def test_sanitize_email_normal(self):
        """Test normal email sanitization."""
        email = "Test@Example.COM"
        result = InputSanitizer.sanitize_email(email)
        assert result == "test@example.com"
    
    def test_sanitize_email_with_dangerous_chars(self):
        """Test email sanitization with dangerous characters."""
        email = "test<script>@example.com"
        result = InputSanitizer.sanitize_email(email)
        assert result == "testscript@example.com"
    
    def test_sanitize_phone_normal(self):
        """Test normal phone sanitization."""
        phone = "+1 (555) 123-4567"
        result = InputSanitizer.sanitize_phone(phone)
        assert result == "+1 (555) 123-4567"
    
    def test_sanitize_phone_with_invalid_chars(self):
        """Test phone sanitization with invalid characters."""
        phone = "+1-555-123-4567 ext. 123"
        result = InputSanitizer.sanitize_phone(phone)
        assert result == "+1-555-123-4567  123"  # Letters removed
    
    def test_sanitize_json_field_email(self):
        """Test JSON field sanitization for email."""
        result = InputSanitizer.sanitize_json_field("Test@Example.COM", "email")
        assert result == "test@example.com"
    
    def test_sanitize_json_field_phone(self):
        """Test JSON field sanitization for phone."""
        result = InputSanitizer.sanitize_json_field("+1-555-123-4567", "phone")
        assert result == "+1-555-123-4567"
    
    def test_sanitize_json_field_string(self):
        """Test JSON field sanitization for generic string."""
        result = InputSanitizer.sanitize_json_field("Normal string", "name")
        assert result == "Normal string"


# Integration test
def test_middleware_integration():
    """Test that middlewares can be integrated into FastAPI app."""
    app = FastAPI()
    
    # Add middlewares
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Test that the app starts and responds
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


if __name__ == "__main__":
    pytest.main([__file__])