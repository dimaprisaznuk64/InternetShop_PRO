import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User
from app.models.category import Category
from app.models.product import Product


async def _setup_order(db_session: AsyncSession):
    cat = Category(name="PayCat", slug="pay-cat")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    product = Product(
        name="PayWidget",
        slug="pay-widget",
        price=50.00,
        sku="PAY-W-1",
        stock=10,
        category_id=cat.id,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product.id


async def _user_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="pay-user-id",
        email="pay@test.com",
        username="payuser",
        hashed_password=hash_password("secret123"),
        role="user",
    ))
    await db_session.commit()
    return create_access_token("pay-user-id")


@pytest.mark.asyncio
async def test_create_payment(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_order(db_session)

    await client.post("/api/cart/items", json={"product_id": prod_id, "quantity": 2}, headers=headers)
    checkout_resp = await client.post("/api/orders/checkout", json={"delivery_address": "Addr"}, headers=headers)
    order_id = checkout_resp.json()["id"]

    response = await client.post(
        "/api/payments/",
        json={"order_id": order_id, "method": "card"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["amount"] == "100.00"
    assert data["method"] == "card"
    assert data["provider_payment_id"].startswith("sim_")


@pytest.mark.asyncio
async def test_create_payment_order_not_found(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/payments/",
        json={"order_id": "nonexistent", "method": "card"},
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_payment_already_paid(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_order(db_session)

    await client.post("/api/cart/items", json={"product_id": prod_id, "quantity": 1}, headers=headers)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers)
    order_id = checkout_resp.json()["id"]

    await client.post("/api/payments/", json={"order_id": order_id, "method": "card"}, headers=headers)

    response = await client.post(
        "/api/payments/",
        json={"order_id": order_id, "method": "card"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_payments(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_order(db_session)

    await client.post("/api/cart/items", json={"product_id": prod_id, "quantity": 1}, headers=headers)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers)
    order_id = checkout_resp.json()["id"]
    await client.post("/api/payments/", json={"order_id": order_id, "method": "card"}, headers=headers)

    response = await client.get("/api/payments/", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_webhook(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_order(db_session)

    await client.post("/api/cart/items", json={"product_id": prod_id, "quantity": 1}, headers=headers)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers)
    order_id = checkout_resp.json()["id"]
    pay_resp = await client.post("/api/payments/", json={"order_id": order_id, "method": "card"}, headers=headers)
    provider_id = pay_resp.json()["provider_payment_id"]

    response = await client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": provider_id, "status": "refunded"},
    )
    assert response.status_code == 200

    pay_resp = await client.get(f"/api/payments/{pay_resp.json()['id']}", headers=headers)
    assert pay_resp.json()["status"] == "refunded"


@pytest.mark.asyncio
async def test_webhook_unknown_provider(client):
    response = await client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": "unknown", "status": "success"},
    )
    assert response.status_code == 404
