from fastapi import FastAPI
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Internet Shop PRO",
    description="Full-featured e-commerce API",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
