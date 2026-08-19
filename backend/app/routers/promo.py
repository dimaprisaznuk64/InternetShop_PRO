from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.promo import PromoCode
from app.schemas.promo import (
    PromoCodeCreate,
    PromoCodeResponse,
    PromoCodeListResponse,
    PromoCodeApply,
)
from app.utils.dependencies import require_admin
from app.utils.exceptions import NotFoundError, AlreadyExistsError, BadRequestError
from app.cache import cache_get, cache_set, cache_delete

router = APIRouter(prefix="/api/promo-codes", tags=["promo codes"])

PROMO_LIST_CACHE_KEY = "promo:list"
PROMO_TTL = 300  # 5 min


@router.get("/", response_model=PromoCodeListResponse)
async def list_promo_codes(
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    cached = await cache_get(PROMO_LIST_CACHE_KEY)
    if cached is not None:
        return PromoCodeListResponse(**cached)

    result = await db.execute(select(PromoCode))
    codes = result.scalars().all()
    data = PromoCodeListResponse(
        promo_codes=[PromoCodeResponse.model_validate(c) for c in codes],
        total=len(codes),
    )
    await cache_set(PROMO_LIST_CACHE_KEY, data.model_dump(), PROMO_TTL)
    return data


@router.post("/", response_model=PromoCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_promo_code(
    data: PromoCodeCreate,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(PromoCode).where(PromoCode.code == data.code))
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("Promo code already exists")

    promo = PromoCode(**data.model_dump())
    db.add(promo)
    await db.commit()
    await db.refresh(promo)

    await cache_delete(PROMO_LIST_CACHE_KEY)
    return promo


@router.post("/apply")
async def apply_promo_code(
    data: PromoCodeApply,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PromoCode).where(PromoCode.code == data.code)
    )
    promo = result.scalar_one_or_none()
    if not promo:
        raise NotFoundError("Promo code not found")

    if not promo.is_active:
        raise BadRequestError("Promo code is inactive")

    if promo.expires_at:
        exp = promo.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            raise BadRequestError("Promo code has expired")

    if promo.max_uses and promo.used_count >= promo.max_uses:
        raise BadRequestError("Promo code usage limit reached")

    return {
        "code": promo.code,
        "discount_type": promo.discount_type.value,
        "discount_value": str(promo.discount_value),
    }


@router.delete("/{promo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promo_code(
    promo_id: str,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PromoCode).where(PromoCode.id == promo_id))
    promo = result.scalar_one_or_none()
    if not promo:
        raise NotFoundError("Promo code not found")

    await db.delete(promo)
    await db.commit()

    await cache_delete(PROMO_LIST_CACHE_KEY)
