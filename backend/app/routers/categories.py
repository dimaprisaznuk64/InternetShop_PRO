from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
)
from app.utils.dependencies import get_current_user, require_admin
from app.utils.exceptions import NotFoundError, AlreadyExistsError
from app.cache import cache_get, cache_set, cache_delete, cache_delete_pattern

router = APIRouter(prefix="/api/categories", tags=["categories"])

CATEGORIES_CACHE_KEY = "categories:list"
CATEGORIES_TTL = 300  # 5 min


@router.get("/", response_model=CategoryListResponse)
async def list_categories(db: AsyncSession = Depends(get_db)):
    cached = await cache_get(CATEGORIES_CACHE_KEY)
    if cached is not None:
        return CategoryListResponse(**cached)

    result = await db.execute(select(Category))
    categories = result.scalars().all()
    data = CategoryListResponse(
        categories=[CategoryResponse.model_validate(c) for c in categories],
        total=len(categories),
    )
    await cache_set(CATEGORIES_CACHE_KEY, data.model_dump(), CATEGORIES_TTL)
    return data


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str, db: AsyncSession = Depends(get_db)):
    cache_key = f"categories:{category_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return CategoryResponse(**cached)

    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundError("Category not found")

    data = CategoryResponse.model_validate(category)
    await cache_set(cache_key, data.model_dump(), CATEGORIES_TTL)
    return data


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    existing = await db.execute(select(Category).where(Category.slug == data.slug))
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("Category with this slug already exists")

    category = Category(**data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)

    await cache_delete(CATEGORIES_CACHE_KEY)
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundError("Category not found")

    existing = await db.execute(
        select(Category).where(Category.slug == data.slug, Category.id != category_id)
    )
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("Category with this slug already exists")

    for key, value in data.model_dump().items():
        setattr(category, key, value)

    await db.commit()
    await db.refresh(category)

    await cache_delete(CATEGORIES_CACHE_KEY)
    await cache_delete(f"categories:{category_id}")
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundError("Category not found")

    await db.delete(category)
    await db.commit()

    await cache_delete(CATEGORIES_CACHE_KEY)
    await cache_delete(f"categories:{category_id}")
