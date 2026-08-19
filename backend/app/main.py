from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.cache import init_redis, close_redis
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

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title="Internet Shop PRO",
    description="Full-featured e-commerce API",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/health")
async def health_check():
    return {"status": "ok"}
