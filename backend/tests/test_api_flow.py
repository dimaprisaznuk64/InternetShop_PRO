import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert, select
from app.models.user import User
from app.models.category import Category
from app.models.product import Product


async def _setup_product(db_session, stock=10, price=25.00):
    cat = Category(name="APICat", slug="api-cat")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    product = Product(
        name="APIWidget", slug="api-widget", price=price,
        sku="API-W-1", stock=stock, category_id=cat.id,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product.id, cat.id


async def _make_user(db_session, uid, email, role="user"):
    await db_session.execute(insert(User).values(
        id=uid, email=email, username=email.split("@")[0],
        hashed_password=hash_password("secret123"), role=role,
    ))
    await db_session.commit()
    return create_access_token(uid)


async def _add_to_cart(client, headers, prod_id, qty=2):
    return await client.post(
        "/api/cart/items",
        json={"product_id": prod_id, "quantity": qty},
        headers=headers,
    )


# Full checkout + payment flow
@pytest.mark.asyncio
async def test_full_checkout_payment_flow(client, db_session):
    token = await _make_user(db_session, "api-u1", "api1@test.com")
    h = {"Authorization": f"Bearer {token}"}
    prod_id, _ = await _setup_product(db_session, stock=10, price=50.00)

    await _add_to_cart(client, h, prod_id, 2)
    checkout = await client.post(
        "/api/orders/checkout",
        json={"delivery_address": "123 Main St", "delivery_method": "courier"},
        headers=h,
    )
    assert checkout.status_code == 201
    order_id = checkout.json()["id"]

    pay_resp = await client.post(
        "/api/payments/",
        json={"order_id": order_id, "method": "card"},
        headers=h,
    )
    assert pay_resp.status_code == 201
    assert pay_resp.json()["status"] == "success"

    order_resp = await client.get(f"/api/orders/{order_id}", headers=h)
    assert order_resp.json()["status"] == "paid"


# Notifications after registration
@pytest.mark.asyncio
async def test_notifications_after_register(client, db_session):
    resp = await client.post("/api/auth/register", json={
        "email": "notif@test.com", "username": "notifuser", "password": "secret123",
    })
    assert resp.status_code == 201

    login = await client.post("/api/auth/login", json={
        "email": "notif@test.com", "password": "secret123",
    })
    h = {"Authorization": f"Bearer {login.json()['access_token']}"}

    notif_resp = await client.get("/api/notifications/", headers=h)
    assert notif_resp.status_code == 200
    assert notif_resp.json()["total"] >= 1
    assert notif_resp.json()["unread_count"] >= 1


# Notifications mark read
@pytest.mark.asyncio
async def test_notification_mark_read(client, db_session):
    token = await _make_user(db_session, "api-u2", "api2@test.com")
    h = {"Authorization": f"Bearer {token}"}

    notifs = await client.get("/api/notifications/", headers=h)
    assert notifs.status_code == 200
    items = notifs.json()["notifications"]
    if items:
        nid = items[0]["id"]
        resp = await client.post(f"/api/notifications/{nid}/read", headers=h)
        assert resp.status_code == 200

        check = await client.get("/api/notifications/", headers=h)
        assert check.json()["unread_count"] == 0


# Notifications mark all read
@pytest.mark.asyncio
async def test_notification_mark_all_read(client, db_session):
    token = await _make_user(db_session, "api-u3", "api3@test.com")
    h = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/notifications/read-all", headers=h)
    assert resp.status_code == 200
    assert resp.json()["marked_read"] >= 0


# Promo apply flow
@pytest.mark.asyncio
async def test_promo_apply_flow(client, db_session):
    admin = await _make_user(db_session, "api-a1", "apia1@test.com", "admin")
    ah = {"Authorization": f"Bearer {admin}"}

    resp = await client.post("/api/promo-codes/", json={
        "code": "TEST10", "discount_type": "percentage",
        "discount_value": 10, "max_uses": 50,
    }, headers=ah)
    assert resp.status_code == 201

    apply = await client.post("/api/promo-codes/apply", json={"code": "TEST10"})
    assert apply.status_code == 200
    assert apply.json()["discount_type"] == "percentage"
    assert apply.json()["discount_value"] == "10.00"


# Favorites flow
@pytest.mark.asyncio
async def test_favorites_flow(client, db_session):
    token = await _make_user(db_session, "api-u4", "api4@test.com")
    h = {"Authorization": f"Bearer {token}"}
    prod_id, _ = await _setup_product(db_session)

    add = await client.post(f"/api/favorites/{prod_id}", headers=h)
    assert add.status_code == 201

    lst = await client.get("/api/favorites/", headers=h)
    assert lst.json()["total"] >= 1

    dup = await client.post(f"/api/favorites/{prod_id}", headers=h)
    assert dup.status_code == 409

    rm = await client.delete(f"/api/favorites/{prod_id}", headers=h)
    assert rm.status_code == 204


# Reviews flow
@pytest.mark.asyncio
async def test_reviews_flow(client, db_session):
    token = await _make_user(db_session, "api-u5", "api5@test.com")
    h = {"Authorization": f"Bearer {token}"}
    prod_id, _ = await _setup_product(db_session)

    rev = await client.post("/api/reviews/", json={
        "product_id": prod_id, "rating": 5, "text": "Great product!",
    }, headers=h)
    assert rev.status_code == 201

    lst = await client.get(f"/api/reviews/product/{prod_id}")
    assert lst.status_code == 200

    dup = await client.post("/api/reviews/", json={
        "product_id": prod_id, "rating": 4, "text": "Good",
    }, headers=h)
    assert dup.status_code == 409


# Admin stats
@pytest.mark.asyncio
async def test_admin_stats(client, db_session):
    admin = await _make_user(db_session, "api-a2", "apia2@test.com", "admin")
    ah = {"Authorization": f"Bearer {admin}"}

    stats = await client.get("/api/admin/stats", headers=ah)
    assert stats.status_code == 200
    data = stats.json()
    assert "total_users" in data
    assert "total_products" in data
    assert "total_orders" in data
    assert "total_revenue" in data


# Admin popular products
@pytest.mark.asyncio
async def test_admin_popular_products(client, db_session):
    admin = await _make_user(db_session, "api-a3", "apia3@test.com", "admin")
    ah = {"Authorization": f"Bearer {admin}"}

    resp = await client.get("/api/admin/popular-products", headers=ah)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# Task status
@pytest.mark.asyncio
async def test_task_stats(client, db_session):
    token = await _make_user(db_session, "api-u6", "api6@test.com")
    h = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/notifications/tasks", headers=h)
    assert resp.status_code == 200
    assert "pending" in resp.json()
    assert "completed" in resp.json()
