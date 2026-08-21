import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User
from app.models.category import Category
from app.models.product import Product


async def _setup_product(db_session: AsyncSession, stock=10, price=25.00):
    cat = Category(name="OrderCat", slug="order-cat")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    product = Product(
        name="OrderWidget",
        slug="order-widget",
        price=price,
        sku="ORD-W-1",
        stock=stock,
        category_id=cat.id,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product.id


async def _user_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="ord-user-id",
        email="ord@test.com",
        username="orduser",
        hashed_password=hash_password("secret123"),
        role="user",
    ))
    await db_session.commit()
    return create_access_token("ord-user-id")


async def _admin_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="ord-admin-id",
        email="ordadmin@test.com",
        username="ordadmin",
        hashed_password=hash_password("secret123"),
        role="admin",
    ))
    await db_session.commit()
    return create_access_token("ord-admin-id")


async def _add_to_cart(client, headers, prod_id, qty=2):
    return await client.post(
        "/api/cart/items",
        json={"product_id": prod_id, "quantity": qty},
        headers=headers,
    )


@pytest.mark.asyncio
async def test_checkout_empty_cart(client, db_session):
    headers = {"Authorization": f"Bearer {await _user_token(db_session)}"}
    response = await client.post(
        "/api/orders/checkout",
        json={"delivery_address": "123 Main St"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_checkout_success(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)

    await _add_to_cart(client, headers, prod_id, qty=2)

    response = await client.post(
        "/api/orders/checkout",
        json={"delivery_address": "123 Main St", "delivery_method": "courier"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["total"] == "100.00"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2

    cart_resp = await client.get("/api/cart/", headers=headers)
    assert cart_resp.json()["items_count"] == 0


@pytest.mark.asyncio
async def test_checkout_deducts_stock(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=5)

    await _add_to_cart(client, headers, prod_id, qty=3)

    await client.post(
        "/api/orders/checkout",
        json={"delivery_address": "Addr"},
        headers=headers,
    )

    from sqlalchemy import select
    from app.models.product import Product
    result = await db_session.execute(select(Product).where(Product.id == prod_id))
    product = result.scalar_one()
    assert product.stock == 2


@pytest.mark.asyncio
async def test_checkout_exceeds_stock(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=2)

    await _add_to_cart(client, headers, prod_id, qty=5)

    response = await client.post(
        "/api/orders/checkout",
        json={"delivery_address": "Addr"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_my_orders(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)

    await _add_to_cart(client, headers, prod_id, qty=1)
    await client.post("/api/orders/checkout", json={}, headers=headers)

    response = await client.get("/api/orders/", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_get_order(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session)

    await _add_to_cart(client, headers, prod_id, qty=1)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers)
    order_id = checkout_resp.json()["id"]

    response = await client.get(f"/api/orders/{order_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == order_id


@pytest.mark.asyncio
async def test_get_order_wrong_user(client, db_session):
    token1 = await _user_token(db_session)
    headers1 = {"Authorization": f"Bearer {token1}"}
    prod_id = await _setup_product(db_session)

    await _add_to_cart(client, headers1, prod_id, qty=1)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers1)
    order_id = checkout_resp.json()["id"]

    await db_session.execute(insert(User).values(
        id="other-ord-user",
        email="other@test.com",
        username="otheruser",
        hashed_password=hash_password("secret123"),
        role="user",
    ))
    await db_session.commit()
    token2 = create_access_token("other-ord-user")
    headers2 = {"Authorization": f"Bearer {token2}"}

    response = await client.get(f"/api/orders/{order_id}", headers=headers2)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_admin_list_orders(client, db_session):
    user_token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {user_token}"}
    prod_id = await _setup_product(db_session)

    await _add_to_cart(client, headers, prod_id, qty=1)
    await client.post("/api/orders/checkout", json={}, headers=headers)

    admin_token = await _admin_token(db_session)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/api/orders/admin/all", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_admin_update_status(client, db_session):
    user_token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {user_token}"}
    prod_id = await _setup_product(db_session)

    await _add_to_cart(client, headers, prod_id, qty=1)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers)
    order_id = checkout_resp.json()["id"]

    admin_token = await _admin_token(db_session)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "paid"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_admin_invalid_status(client, db_session):
    user_token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {user_token}"}
    prod_id = await _setup_product(db_session)

    await _add_to_cart(client, headers, prod_id, qty=1)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers)
    order_id = checkout_resp.json()["id"]

    admin_token = await _admin_token(db_session)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "bogus"},
        headers=admin_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_user_cannot_update_status(client, db_session):
    user_token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {user_token}"}
    prod_id = await _setup_product(db_session)

    await _add_to_cart(client, headers, prod_id, qty=1)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers)
    order_id = checkout_resp.json()["id"]

    response = await client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "paid"},
        headers=headers,
    )
    assert response.status_code == 403


async def _create_promo(db_session: AsyncSession, code="PROMO10", discount_type="percentage",
                        discount_value=10, min_order_amount=None, max_uses=None,
                        expires_at=None, is_active=True, used_count=0):
    from app.models.promo import PromoCode
    promo = PromoCode(
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        min_order_amount=min_order_amount,
        max_uses=max_uses,
        expires_at=expires_at,
        is_active=is_active,
        used_count=used_count,
    )
    db_session.add(promo)
    await db_session.commit()
    await db_session.refresh(promo)
    return promo


@pytest.mark.asyncio
async def test_checkout_applies_percentage_promo(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)
    await _create_promo(db_session, code="TAKE20", discount_type="percentage", discount_value=20)

    await _add_to_cart(client, headers, prod_id, qty=2)

    response = await client.post(
        "/api/orders/checkout",
        json={"promo_code": "TAKE20"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["discount"] == "20.00"
    assert data["total"] == "80.00"


@pytest.mark.asyncio
async def test_checkout_applies_fixed_promo(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)
    await _create_promo(db_session, code="FLAT30", discount_type="fixed", discount_value=30)

    await _add_to_cart(client, headers, prod_id, qty=2)

    response = await client.post(
        "/api/orders/checkout",
        json={"promo_code": "FLAT30"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["discount"] == "30.00"
    assert data["total"] == "70.00"


@pytest.mark.asyncio
async def test_checkout_fixed_promo_cannot_go_negative(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)
    await _create_promo(db_session, code="HUGE500", discount_type="fixed", discount_value=500)

    await _add_to_cart(client, headers, prod_id, qty=1)

    response = await client.post(
        "/api/orders/checkout",
        json={"promo_code": "HUGE500"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total"] == "0.00"
    assert data["discount"] == "50.00"


@pytest.mark.asyncio
async def test_checkout_promo_increments_used_count(client, db_session):
    from sqlalchemy import select
    from app.models.promo import PromoCode
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)
    promo = await _create_promo(db_session, code="COUNTME", discount_type="fixed", discount_value=5)

    await _add_to_cart(client, headers, prod_id, qty=1)
    response = await client.post(
        "/api/orders/checkout",
        json={"promo_code": "COUNTME"},
        headers=headers,
    )
    assert response.status_code == 201

    result = await db_session.execute(select(PromoCode).where(PromoCode.code == "COUNTME"))
    refreshed = result.scalar_one()
    assert refreshed.used_count == 1


@pytest.mark.asyncio
async def test_checkout_rejects_expired_promo(client, db_session):
    from datetime import datetime, UTC
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)
    await _create_promo(db_session, code="OLDIE", discount_type="percentage",
                        discount_value=50, expires_at=datetime(2020, 1, 1, tzinfo=UTC))

    await _add_to_cart(client, headers, prod_id, qty=1)

    response = await client.post(
        "/api/orders/checkout",
        json={"promo_code": "OLDIE"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_rejects_inactive_promo(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)
    await _create_promo(db_session, code="DEAD", discount_type="percentage",
                        discount_value=50, is_active=False)

    await _add_to_cart(client, headers, prod_id, qty=1)

    response = await client.post(
        "/api/orders/checkout",
        json={"promo_code": "DEAD"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_rejects_exhausted_promo(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)
    await _create_promo(db_session, code="SPENT", discount_type="percentage",
                        discount_value=50, max_uses=1, used_count=1)

    await _add_to_cart(client, headers, prod_id, qty=1)

    response = await client.post(
        "/api/orders/checkout",
        json={"promo_code": "SPENT"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_rejects_promo_below_min_order(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)
    await _create_promo(db_session, code="BIGONLY", discount_type="percentage",
                        discount_value=10, min_order_amount=1000)

    await _add_to_cart(client, headers, prod_id, qty=1)

    response = await client.post(
        "/api/orders/checkout",
        json={"promo_code": "BIGONLY"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "at least" in response.json()["detail"]


@pytest.mark.asyncio
async def test_checkout_unknown_promo_rejected(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_product(db_session, stock=10, price=50.00)

    await _add_to_cart(client, headers, prod_id, qty=1)

    response = await client.post(
        "/api/orders/checkout",
        json={"promo_code": "GHOST"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]
