# Rate Limiting and Request Validation Middleware

This document describes the rate limiting and request validation middleware implemented for the HotelAgent authentication system.

## Overview

The system implements two key middleware components:

1. **Rate Limiting Middleware** - Provides brute force protection and API rate limiting
2. **Request Validation Middleware** - Validates and sanitizes incoming requests

## Rate Limiting Middleware

### Features

- **General API Rate Limiting**: 100 requests per hour per IP
- **Authentication Endpoint Limiting**: 5 attempts per 15 minutes per IP
- **Brute Force Protection**: Progressive blocking for repeated failures
- **IP-based Blocking**: Automatic IP blocking for suspicious activity
- **Redis Backend**: Distributed rate limiting using Redis

### Configuration

```python
# In settings/base.py
RATE_LIMIT_REQUESTS = 100  # General API limit
RATE_LIMIT_WINDOW = 3600   # 1 hour window
RATE_LIMIT_LOGIN_ATTEMPTS = 5  # Auth attempts limit
RATE_LIMIT_LOGIN_WINDOW = 900  # 15 minutes window
```

### Usage

```python
from app.middleware.rate_limit import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    auth_endpoints=["/api/v1/auth/login", "/api/v1/auth/refresh"]
)
```

### Blocking Periods

The system implements progressive blocking:

1. **First block**: 5 minutes
2. **Second block**: 15 minutes  
3. **Third block**: 1 hour
4. **Fourth block**: 2 hours
5. **Subsequent blocks**: 24 hours

### Response Headers

Rate limited responses include:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1641234567
Retry-After: 3600
```

## Request Validation Middleware

### Features

- **Request Size Validation**: Maximum 10MB request size
- **Content Type Validation**: Allowed content types only
- **JSON Depth Validation**: Maximum 10 levels deep
- **SQL Injection Detection**: Pattern-based detection
- **XSS Prevention**: Script and HTML tag detection
- **Path Traversal Detection**: Directory traversal prevention
- **Input Sanitization**: Automatic field sanitization

### Security Patterns

#### SQL Injection Detection
- SQL keywords (SELECT, INSERT, UPDATE, DELETE, etc.)
- Comment patterns (--, #, /* */)
- Boolean logic patterns (OR 1=1, AND 1=1)
- System table references (INFORMATION_SCHEMA, etc.)

#### XSS Detection
- Script tags (`<script>`, `</script>`)
- JavaScript URLs (`javascript:`)
- Event handlers (`onclick=`, `onload=`, etc.)
- Iframe, object, embed tags

#### Path Traversal Detection
- Directory traversal patterns (`../`, `..\\`)
- URL encoded traversal (`%2e%2e%2f`)

### Usage

```python
from app.middleware.validation import RequestValidationMiddleware

app.add_middleware(
    RequestValidationMiddleware,
    max_request_size=10 * 1024 * 1024,  # 10MB
    max_json_depth=10
)
```

### Input Sanitization

The middleware includes an `InputSanitizer` class for field-specific sanitization:

```python
from app.middleware.validation import input_sanitizer

# Sanitize email
clean_email = input_sanitizer.sanitize_email("Test@Example.COM")
# Result: "test@example.com"

# Sanitize phone
clean_phone = input_sanitizer.sanitize_phone("+1 (555) 123-4567")
# Result: "+1 (555) 123-4567"

# Sanitize string
clean_string = input_sanitizer.sanitize_string("String with\x00null")
# Result: "String withnull"
```

## Brute Force Protection

### Standalone Usage

The brute force protection can be used independently:

```python
from app.middleware.rate_limit import brute_force_protection

# Record login attempt
await brute_force_protection.record_login_attempt(
    identifier="user@example.com",
    success=False,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)

# Check if blocked
block_status = await brute_force_protection.is_blocked(
    identifier="user@example.com",
    ip_address="192.168.1.1"
)

if block_status["blocked"]:
    print(f"Blocked: {block_status['reason']}")
    print(f"Retry after: {block_status['retry_after']} seconds")
```

### Integration with Authentication

The login endpoint automatically integrates with brute force protection:

```python
# In auth routes
from app.middleware.rate_limit import brute_force_protection

@router.post("/login")
async def login(request: Request, login_data: LoginRequest):
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    
    # Check for brute force protection
    block_status = await brute_force_protection.is_blocked(
        identifier=login_data.email,
        ip_address=client_ip
    )
    
    if block_status["blocked"]:
        raise HTTPException(
            status_code=429,
            detail=block_status["reason"]
        )
    
    # ... authentication logic ...
    
    # Record attempt result
    await brute_force_protection.record_login_attempt(
        identifier=login_data.email,
        success=success,
        ip_address=client_ip,
        user_agent=user_agent
    )
```

## Error Responses

### Rate Limit Exceeded

```json
{
    "error_code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "timestamp": "2025-01-09T10:30:00Z"
}
```

### Brute Force Detected

```json
{
    "error_code": "BRUTE_FORCE_DETECTED", 
    "message": "Too many failed attempts detected",
    "timestamp": "2025-01-09T10:30:00Z"
}
```

### Validation Error

```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": "Invalid JSON content",
    "timestamp": "2025-01-09T10:30:00Z"
}
```

## Monitoring and Logging

### Audit Events

The middleware automatically logs security events:

- `rate_limit_exceeded` - Rate limit violations
- `brute_force_detected` - Brute force attempts
- `login_blocked_brute_force` - Blocked login attempts
- `invalid_request_content` - Malicious content detection

### Log Examples

```
2025-01-09 10:30:00 - WARNING - Rate limit exceeded - IP: 192.168.1.1
2025-01-09 10:31:00 - ERROR - Brute force attack detected - IP: 192.168.1.1
2025-01-09 10:32:00 - WARNING - Malicious content detected in JSON body
```

## Redis Keys

The middleware uses the following Redis key patterns:

### Rate Limiting
- `rate_limit:general:{ip}` - General API rate limiting
- `rate_limit:auth:{ip}` - Authentication rate limiting
- `rate_violations:{ip}` - Rate limit violations

### Brute Force Protection
- `failed_attempts:{ip}` - Failed attempt tracking
- `blocked_ip:{ip}` - IP block information
- `block_count:{ip}` - Block count tracking
- `login_attempts:user:{email}` - User-specific attempts
- `login_attempts:ip:{ip}` - IP-specific attempts

## Configuration Examples

### Development Environment

```python
# Relaxed settings for development
RATE_LIMIT_REQUESTS = 1000
RATE_LIMIT_LOGIN_ATTEMPTS = 10
RATE_LIMIT_LOGIN_WINDOW = 300  # 5 minutes
```

### Production Environment

```python
# Strict settings for production
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_LOGIN_ATTEMPTS = 5
RATE_LIMIT_LOGIN_WINDOW = 900  # 15 minutes
```

## Testing

Run the middleware tests:

```bash
python -m pytest hotel_agent/tests/test_rate_limit_validation.py -v
```

## Performance Considerations

1. **Redis Performance**: Use Redis clustering for high-traffic scenarios
2. **Middleware Order**: Place validation middleware before rate limiting
3. **Async Operations**: All Redis operations are async to prevent blocking
4. **Pattern Compilation**: Security patterns are pre-compiled for performance
5. **Error Handling**: Graceful degradation when Redis is unavailable

## Security Best Practices

1. **IP Whitelisting**: Consider whitelisting trusted IPs
2. **Threat Intelligence**: Integrate with threat intelligence feeds
3. **Monitoring**: Set up alerts for repeated violations
4. **Log Analysis**: Regularly analyze logs for attack patterns
5. **Rate Limit Tuning**: Adjust limits based on legitimate usage patterns

## Troubleshooting

### Common Issues

1. **Redis Connection**: Ensure Redis is running and accessible
2. **High Memory Usage**: Monitor Redis memory usage and set appropriate TTLs
3. **False Positives**: Adjust rate limits if legitimate users are blocked
4. **Performance Impact**: Monitor response times with middleware enabled

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger("app.middleware").setLevel(logging.DEBUG)
```