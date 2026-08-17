from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers.auth import router as auth_router

settings = get_settings()

app = FastAPI(
    title="Internet Shop PRO",
    description="Full-featured e-commerce API",
    version="0.1.0",
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
