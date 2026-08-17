import uuid
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.promo import PromoCode, DiscountType


def test_user_creation():
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        role=UserRole.user,
        is_active=True,
    )
    assert user.email == "test@example.com"
    assert user.role == UserRole.user
    assert user.is_active is True


def test_user_roles():
    assert UserRole.user.value == "user"
    assert UserRole.manager.value == "manager"
    assert UserRole.admin.value == "admin"


def test_category_creation():
    cat = Category(
        id=str(uuid.uuid4()),
        name="Electronics",
        slug="electronics",
    )
    assert cat.name == "Electronics"
    assert cat.slug == "electronics"
    assert cat.parent_id is None


def test_category_with_parent():
    parent = Category(id=str(uuid.uuid4()), name="Phones", slug="phones")
    child = Category(
        id=str(uuid.uuid4()),
        name="Smartphones",
        slug="smartphones",
        parent_id=parent.id,
    )
    assert child.parent_id == parent.id


def test_product_creation():
    product = Product(
        id=str(uuid.uuid4()),
        name="iPhone 16",
        slug="iphone-16",
        price=999.99,
        sku="IPH-16-001",
        stock=50,
        category_id=str(uuid.uuid4()),
        is_active=True,
    )
    assert product.name == "iPhone 16"
    assert float(product.price) == 999.99
    assert product.stock == 50
    assert product.is_active is True


def test_promo_code_types():
    assert DiscountType.percentage.value == "percentage"
    assert DiscountType.fixed.value == "fixed"


def test_promo_code_creation():
    promo = PromoCode(
        id=str(uuid.uuid4()),
        code="WELCOME10",
        discount_type=DiscountType.percentage,
        discount_value=10,
        is_active=True,
    )
    assert promo.code == "WELCOME10"
    assert promo.discount_type == DiscountType.percentage
    assert float(promo.discount_value) == 10
    assert promo.is_active is True
