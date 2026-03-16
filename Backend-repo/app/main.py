"""
FastAPI main application - simplified for testing.
"""

import random
import logging
from contextlib import asynccontextmanager
 
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .utils.exceptions import ( # noqa: F401
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    InvalidCredentialsError,
    InvalidTokenError,
    AccountLockedError,
    InsufficientPermissionsError,
    DataSegregationError,
    RoleHierarchyError,
    FeatureAccessError,
    ValidationError as CustomValidationError,
    RateLimitExceededError,
    BruteForceDetectedError
)
from dotenv import load_dotenv
 
from .settings.base import get_settings
from .routers import public_api_router, internal_api_router, APIRouter
from .routes.hotel.section import section_router
from .routes.hotel.table import table_router
from .routes.hotel.hall import hall_router # Import the new hall router
from .routes.hotel.branch import branch_management_router # Import the branch router
from .routes.dashboard import router as dashboard_router
from .routes.notifications import router as notification_router
from .routes.hotel.floor import router as floor_router
from .routes.facility.menu import router as menu_router # NEW: Import the menu router
from .core.dependencies import get_dev_docs_user # Import from the new location
from .models.core.auth import Base
from .middleware.audit import AuditMiddleware
from .middleware.auth import JWTAuthenticationMiddleware
from .middleware.rbac import DataSegregationMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.validation import RequestValidationMiddleware
from .settings.constants import RoleNames
from .subscription_service import check_and_expire_subscriptions
from .core.audit import audit_service, extract_ip_address, extract_user_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
 
# Load environment variables from .env file
load_dotenv()
 
settings = get_settings()
 
scheduler = AsyncIOScheduler(timezone="UTC")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Calculate some fun facts about the project
    public_routes = len(public_api_router.routes)
    internal_routes = len(internal_api_router.routes) + len(internal_hotel_management_router.routes)
    public_hotel_routes = len(public_hotel_management_router.routes)
    total_routes = public_routes + internal_routes + public_hotel_routes
    
    # ASCII Art Banner
    # ASCII Art Banner
    banner = r"""
███████╗ █████╗ ███████╗████████╗ █████╗ ██████╗ ██╗
██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║
█████╗  ███████║███████╗   ██║   ███████║██████╔╝██║
██╔══╝  ██╔══██║╚════██║   ██║   ██╔══██║██╔═══╝ ██║
██║     ██║  ██║███████║   ██║   ██║  ██║██║     ██║
╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝
"""

    
    logger.info(banner)
    logger.info("="*70)
    logger.info(f"🚀 Starting HotelAgent API server... Found {total_routes} total routes ({public_routes + public_hotel_routes} public, {internal_routes} internal).")
    logger.info("="*70)

    from .core.database import create_tables

    # Schedule the background job to run once every 24 hours
    scheduler.add_job(
        check_and_expire_subscriptions,
        'interval',
        hours=24,
        id="expire_subscriptions_job"
    )
    scheduler.start()
    logger.info("Subscription expiration job has been scheduled to run daily.")
    # await create_tables()
    yield
    logger.info("Shutting down HotelAgent API server...")
    scheduler.shutdown()

 
# Create FastAPI application
app = FastAPI(
    title="HotelAgent API",
    description="Public API for the Multi-tenant hotel management system.",
    version="1.0.0",
    lifespan=lifespan,
    # The default docs_url is /docs, which will now show the public API
    redoc_url=None, # Disable Redoc for simplicity
)
 

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)
 
# Include routers
# Public APIs are included normally and will appear in the default /docs
app.include_router(public_api_router, prefix="/api/v1")
app.include_router(internal_api_router, prefix="/api/v1", include_in_schema=False)
 
# --- Hotel Management Router Aggregation (Split for Public/Internal Docs) ---

# 1. Router for APIs that should be PUBLIC
public_hotel_management_router = APIRouter()
public_hotel_management_router.include_router(branch_management_router, tags=["Branch Management"])
public_hotel_management_router.include_router(floor_router, tags=["Floors"])
public_hotel_management_router.include_router(hall_router, tags=["Halls"])
public_hotel_management_router.include_router(section_router, tags=["Section Management"])
public_hotel_management_router.include_router(table_router, tags=["Table Management"])


# 2. Router for APIs that are INTERNAL-ONLY (Work-In-Progress)
internal_hotel_management_router = APIRouter()
 
# Include the public hotel router in the main app (visible in /docs)
app.include_router(public_hotel_management_router, prefix="/api/v1/hotels")

# Make Dashboard and Notifications public
app.include_router(dashboard_router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(notification_router, prefix="/api/v1", tags=["Notifications"])

# NEW: Facility Management Router Aggregation
facility_management_router = APIRouter()
facility_management_router.include_router(menu_router, tags=["Menu Management"])

# Include the facility router in the main app with a specific prefix.
app.include_router(facility_management_router, prefix="/api/v1/facility")

# Include the internal hotel router but hide it from public docs
app.include_router(internal_hotel_management_router, prefix="/api/v1/hotels", include_in_schema=False)
 

@app.get("/work-in-progress-APIs", include_in_schema=False)
async def get_wip_swagger_documentation(
    username: str = Depends(get_dev_docs_user),
):
    """Serves the Swagger UI for Work-In-Progress documentation."""
    return get_swagger_ui_html(
        openapi_url="/wip-openapi.json", title="Work-In-Progress API Docs"
    )
 
@app.get("/wip-openapi.json", include_in_schema=False)
async def get_wip_open_api_endpoint(
    username: str = Depends(get_dev_docs_user),
):
    """Generates the OpenAPI schema for all work-in-progress and public endpoints."""
    # Create a temporary app to generate the full schema, bypassing the `include_in_schema=False`
    # on the main app instance. This ensures all routes are included in the WIP docs.
    temp_app = FastAPI(
        title="HotelAgent API - Internal",
        version=app.version, # type: ignore
    )
    temp_app.include_router(public_api_router, prefix="/api/v1")
    temp_app.include_router(internal_api_router, prefix="/api/v1")
    # Include both public and internal hotel routers for the complete WIP docs
    temp_app.include_router(public_hotel_management_router, prefix="/api/v1/hotels")
    temp_app.include_router(internal_hotel_management_router, prefix="/api/v1/hotels")
    
    # Manually add health check routes to the temporary app for documentation
    temp_app.get("/health", tags=["default"])(health_check)
    temp_app.get("/ready", tags=["default"])(readiness_check)

    return JSONResponse(
        get_openapi(title=temp_app.title, version=temp_app.version, routes=temp_app.routes)
    )

# --- MIDDLEWARE CONFIGURATION ---
# The order of middleware is crucial. It should be:
# 1. CORS (to handle preflight OPTIONS requests first)
# 2. Rate Limiting / Validation (early rejection of invalid requests)
# 3. Audit (to log all incoming requests)
# 4. Authentication (to populate request.state.user)
# 5. Authorization/RBAC (to check permissions based on user)

# 1. CORS Middleware (MUST BE FIRST)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
#     allow_methods=settings.CORS_ALLOW_METHODS,
#     allow_headers=settings.CORS_ALLOW_HEADERS,
# )

# 2. Add other custom middleware in the correct order
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(JWTAuthenticationMiddleware)
app.add_middleware(DataSegregationMiddleware)

# Add a global OPTIONS handler to work with Nginx-based CORS
# This must be added AFTER all other middleware.
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str) -> Response:
    """
    Handles all preflight OPTIONS requests globally.
    This is necessary when CORS is handled by a reverse proxy (Nginx).
    """
    return Response(status_code=status.HTTP_200_OK)


# Simple exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error_code": "AUTHENTICATION_ERROR",
            "message": "Authentication failed",
            "details": str(exc) if settings.DEBUG else None
        }
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    """Handle invalid credentials errors."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error_code": "INVALID_CREDENTIALS",
            "message": "Invalid username or password"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail
        },
        headers=exc.headers
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.DEBUG else None
        }
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready"}

import logging, traceback
from fastapi import Request
from fastapi.responses import PlainTextResponse

logger = logging.getLogger("uvicorn.error")

@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error("Unhandled exception:\n%s", tb)
    return PlainTextResponse("Internal Server Error", status_code=500)