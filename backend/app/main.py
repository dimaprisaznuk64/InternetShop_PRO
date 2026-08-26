import asyncio
import logging
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
from app.config import get_settings
from app.cache import init_redis, close_redis, get_redis
from app.services.background import task_manager, cleanup_service
from app.middleware import SecurityHeadersMiddleware, RateLimitMiddleware
from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.routers.categories import router as categories_router
from app.routers.products import router as products_router
from app.routers.product_images import router as product_images_router
from app.routers.product_variants import router as product_variants_router
from app.routers.cart import router as cart_router
from app.routers.orders import router as orders_router
from app.routers.payments import router as payments_router
from app.routers.favorites import router as favorites_router
from app.routers.reviews import router as reviews_router
from app.routers.promo import router as promo_router
from app.routers.admin import router as admin_router
from app.routers.notifications import router as notifications_router
from app.routers.ws import router as ws_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    await task_manager.start()
    await cleanup_service.start()
    yield
    await cleanup_service.stop()
    await task_manager.stop()
    await close_redis()


_docs = "/docs" if settings.DEBUG else None
_redoc = "/redoc" if settings.DEBUG else None
_openapi = "/openapi.json" if settings.DEBUG else None

app = FastAPI(
    title="Internet Shop PRO",
    description="Full-featured e-commerce API",
    version="1.0.1",
    debug=settings.DEBUG,
    docs_url=_docs,
    redoc_url=_redoc,
    openapi_url=_openapi,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

if settings.ALLOWED_HOSTS.strip() != "*":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list,
    )

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(product_images_router)
app.include_router(product_variants_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(favorites_router)
app.include_router(reviews_router)
app.include_router(promo_router)
app.include_router(admin_router)
app.include_router(notifications_router)
app.include_router(ws_router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "Operation conflicts with existing data"},
    )


from app.utils.dependencies import UnauthorizedError


@app.exception_handler(UnauthorizedError)
async def unauthorized_error_handler(request: Request, exc: UnauthorizedError):
    return JSONResponse(
        status_code=401,
        content={"detail": exc.detail},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
async def health_check():
    redis = await get_redis()
    redis_status = "disconnected"
    if redis:
        try:
            await redis.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"

    celery_status = "not_configured"
    try:
        from app.celery_app import celery_app
        inspect = celery_app.control.inspect(timeout=1.0)
        active = inspect.active()
        if active is not None:
            celery_status = "connected"
        else:
            celery_status = "no_workers"
    except Exception:
        celery_status = "unavailable"

    return {"status": "ok", "redis": redis_status, "celery": celery_status}
