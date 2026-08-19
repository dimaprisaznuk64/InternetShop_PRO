import uuid
import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.models.promo import PromoCode, PromoDiscountType
from app.utils.security import hash_password


class UserFactory:
    @staticmethod
    async def create(
        db: AsyncSession,
        email: Optional[str] = None,
        username: Optional[str] = None,
        password: str = "testpass123",
        role: UserRole = UserRole.user,
        is_active: bool = True,
    ) -> User:
        uid = str(uuid.uuid4())[:8]
        user = User(
            email=email or f"user-{uid}@test.com",
            username=username or f"user-{uid}",
            hashed_password=hash_password(password),
            role=role,
            is_active=is_active,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def create_admin(db: AsyncSession, **kwargs) -> User:
        return await UserFactory.create(db, role=UserRole.admin, **kwargs)

    @staticmethod
    async def create_manager(db: AsyncSession, **kwargs) -> User:
        return await UserFactory.create(db, role=UserRole.manager, **kwargs)


class CategoryFactory:
    @staticmethod
    async def create(
        db: AsyncSession,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        description: str = "Test category",
        parent_id: Optional[str] = None,
    ) -> Category:
        uid = str(uuid.uuid4())[:8]
        cat = Category(
            name=name or f"Category {uid}",
            slug=slug or f"category-{uid}",
            description=description,
            parent_id=parent_id,
        )
        db.add(cat)
        await db.commit()
        await db.refresh(cat)
        return cat


class ProductFactory:
    @staticmethod
    async def create(
        db: AsyncSession,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        sku: Optional[str] = None,
        price: float = 29.99,
        stock: int = 100,
        category_id: Optional[str] = None,
        brand: str = "TestBrand",
        description: str = "Test product",
    ) -> Product:
        uid = str(uuid.uuid4())[:8]
        product = Product(
            name=name or f"Product {uid}",
            slug=slug or f"product-{uid}",
            sku=sku or f"SKU-{uid}",
            price=price,
            stock=stock,
            category_id=category_id,
            brand=brand,
            description=description,
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product


class OrderFactory:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        total: float = 99.99,
        status: OrderStatus = OrderStatus.pending,
        delivery_method: str = "standard",
        delivery_address: str = "123 Test St",
    ) -> Order:
        order = Order(
            user_id=user_id,
            total=total,
            status=status,
            delivery_method=delivery_method,
            delivery_address=delivery_address,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order


class PromoFactory:
    @staticmethod
    async def create(
        db: AsyncSession,
        code: Optional[str] = None,
        discount_type: PromoDiscountType = PromoDiscountType.percentage,
        discount_value: float = 10.0,
        max_uses: int = 100,
        is_active: bool = True,
    ) -> PromoCode:
        uid = str(uuid.uuid4())[:8]
        promo = PromoCode(
            code=code or f"PROMO-{uid}",
            discount_type=discount_type,
            discount_value=discount_value,
            max_uses=max_uses,
            is_active=is_active,
        )
        db.add(promo)
        await db.commit()
        await db.refresh(promo)
        return promo
