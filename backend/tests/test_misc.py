import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from datetime import datetime, timedelta, timezone


async def _setup_product(db_session: AsyncSession):
    cat = Category(name="MiscCat", slug="misc-cat")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    product = Product(name="Widget", slug="misc-widget", price=10.00, sku="MSC-W-1", stock=5, category_id=cat.id)
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product.id


async def _user_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="misc-user-id", email="misc@test.com", username="miscuser",
        hashed_password=hash_password("secret123"), role="user",
    ))
    await db_session.commit()
    return create_access_token("misc-user-id")


async def _admin_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="misc-admin-id", email="miscadmin@test.com", username="miscadmin",
        hashed_password=hash_password("secret123"), role="admin",
    ))
    await db_session.commit()
    return create_access_token("misc-admin-id")


# === FAVORITES ===

@pytest.mark.asyncio
async def test_add_favorite(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)

    resp = await client.post(f"/api/favorites/{prod_id}", headers=headers)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_list_favorites(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)
    await client.post(f"/api/favorites/{prod_id}", headers=headers)

    resp = await client.get("/api/favorites/", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_remove_favorite(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)
    await client.post(f"/api/favorites/{prod_id}", headers=headers)

    resp = await client.delete(f"/api/favorites/{prod_id}", headers=headers)
    assert resp.status_code == 204

    list_resp = await client.get("/api/favorites/", headers=headers)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_duplicate_favorite(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)
    await client.post(f"/api/favorites/{prod_id}", headers=headers)

    resp = await client.post(f"/api/favorites/{prod_id}", headers=headers)
    assert resp.status_code == 409


# === REVIEWS ===

@pytest.mark.asyncio
async def test_create_review(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)

    resp = await client.post(
        "/api/reviews/",
        json={"product_id": prod_id, "rating": 5, "text": "Great!"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["rating"] == 5


@pytest.mark.asyncio
async def test_duplicate_review(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)
    await client.post("/api/reviews/", json={"product_id": prod_id, "rating": 4}, headers=headers)

    resp = await client.post("/api/reviews/", json={"product_id": prod_id, "rating": 3}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_reviews_unmoderated(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)
    await client.post("/api/reviews/", json={"product_id": prod_id, "rating": 5}, headers=headers)

    resp = await client.get(f"/api/reviews/product/{prod_id}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_moderate_review(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)
    review_resp = await client.post("/api/reviews/", json={"product_id": prod_id, "rating": 4}, headers=headers)
    review_id = review_resp.json()["id"]

    admin_token = await _admin_token(db_session)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.patch(f"/api/reviews/{review_id}/moderate", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["is_moderated"] is True

    list_resp = await client.get(f"/api/reviews/product/{prod_id}")
    assert list_resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_delete_review(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)
    review_resp = await client.post("/api/reviews/", json={"product_id": prod_id, "rating": 3}, headers=headers)
    review_id = review_resp.json()["id"]

    resp = await client.delete(f"/api/reviews/{review_id}", headers=headers)
    assert resp.status_code == 204


# === PROMO CODES ===

@pytest.mark.asyncio
async def test_create_promo_code(client, db_session):
    admin_token = await _admin_token(db_session)
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = await client.post(
        "/api/promo-codes/",
        json={"code": "WELCOME10", "discount_type": "percentage", "discount_value": 10},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["code"] == "WELCOME10"


@pytest.mark.asyncio
async def test_apply_promo_code(client, db_session):
    admin_token = await _admin_token(db_session)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post(
        "/api/promo-codes/",
        json={"code": "SALE20", "discount_type": "fixed", "discount_value": 20},
        headers=admin_headers,
    )

    resp = await client.post("/api/promo-codes/apply", json={"code": "SALE20"})
    assert resp.status_code == 200
    assert resp.json()["discount_value"] == "20.00"


@pytest.mark.asyncio
async def test_apply_expired_promo(client, db_session):
    admin_token = await _admin_token(db_session)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post(
        "/api/promo-codes/",
        json={
            "code": "OLD",
            "discount_type": "percentage",
            "discount_value": 50,
            "expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        },
        headers=admin_headers,
    )

    resp = await client.post("/api/promo-codes/apply", json={"code": "OLD"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_promo_codes(client, db_session):
    admin_token = await _admin_token(db_session)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post(
        "/api/promo-codes/",
        json={"code": "TEST", "discount_type": "percentage", "discount_value": 5},
        headers=admin_headers,
    )
    resp = await client.get("/api/promo-codes/", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_user_cannot_create_promo(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/promo-codes/",
        json={"code": "NOPE", "discount_type": "percentage", "discount_value": 10},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_review_verified_purchase_flag(client, db_session):
    from app.models.order import Order, OrderItem, OrderStatus
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)

    order = Order(
        user_id="misc-user-id",
        status=OrderStatus.completed,
        total=50.00,
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(OrderItem(
        order_id=order.id,
        product_id=prod_id,
        quantity=1,
        price=50.00,
    ))
    await db_session.commit()

    resp = await client.post(
        "/api/reviews/",
        json={"product_id": prod_id, "rating": 5, "text": "Bought it, love it"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["is_verified_purchase"] is True


@pytest.mark.asyncio
async def test_review_unverified_without_purchase(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)

    resp = await client.post(
        "/api/reviews/",
        json={"product_id": prod_id, "rating": 4, "text": "No purchase"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["is_verified_purchase"] is False


@pytest.mark.asyncio
async def test_review_cancelled_order_not_verified(client, db_session):
    from app.models.order import Order, OrderItem, OrderStatus
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)

    order = Order(
        user_id="misc-user-id",
        status=OrderStatus.cancelled,
        total=50.00,
    )
    db_session.add(order)
    await db_session.flush()
    db_session.add(OrderItem(
        order_id=order.id,
        product_id=prod_id,
        quantity=1,
        price=50.00,
    ))
    await db_session.commit()

    resp = await client.post(
        "/api/reviews/",
        json={"product_id": prod_id, "rating": 3},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["is_verified_purchase"] is False
