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


@pytest.mark.asyncio
async def test_webhook_idempotent_no_duplicate_side_effects(client, db_session):
    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_order(db_session)

    await client.post("/api/cart/items", json={"product_id": prod_id, "quantity": 1}, headers=headers)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers)
    order_id = checkout_resp.json()["id"]
    pay_resp = await client.post("/api/payments/", json={"order_id": order_id, "method": "card"}, headers=headers)
    provider_id = pay_resp.json()["provider_payment_id"]

    # create_payment already marks payment as success -> success webhook is a replay
    first = await client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": provider_id, "status": "success"},
    )
    assert first.status_code == 200
    assert first.json()["idempotent"] is True

    # refund transitions to a new state -> side effects run once
    refund = await client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": provider_id, "status": "refunded"},
    )
    assert refund.status_code == 200
    assert refund.json() == {"status": "ok"}

    # repeated refund webhook -> no duplicate side effects
    refund_again = await client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": provider_id, "status": "refunded"},
    )
    assert refund_again.status_code == 200
    assert refund_again.json()["idempotent"] is True


@pytest.mark.asyncio
async def test_webhook_rejects_unknown_status(client, db_session):
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
        json={"provider_payment_id": provider_id, "status": "teleported"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_prod_requires_secret(client, db_session, monkeypatch):
    from app.routers import payments as payments_module

    monkeypatch.setattr(payments_module.settings.__class__, "is_production",
                        property(lambda self: True))
    monkeypatch.setattr(payments_module.settings, "WEBHOOK_SECRET", "")

    response = await client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": "whatever", "status": "success"},
    )
    assert response.status_code == 400
    assert "secret" in response.json()["detail"]


@pytest.mark.asyncio
async def test_webhook_valid_and_invalid_signature(client, db_session, monkeypatch):
    import hmac as hmac_mod
    import hashlib as hashlib_mod
    from app.routers import payments as payments_module

    secret = "test-webhook-secret"
    monkeypatch.setattr(payments_module.settings, "WEBHOOK_SECRET", secret)

    token = await _user_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = await _setup_order(db_session)

    await client.post("/api/cart/items", json={"product_id": prod_id, "quantity": 1}, headers=headers)
    checkout_resp = await client.post("/api/orders/checkout", json={}, headers=headers)
    order_id = checkout_resp.json()["id"]
    pay_resp = await client.post("/api/payments/", json={"order_id": order_id, "method": "card"}, headers=headers)
    provider_id = pay_resp.json()["provider_payment_id"]

    bad_sig = hmac_mod.new(b"wrong-secret", f"{provider_id}:success".encode(), hashlib_mod.sha256).hexdigest()
    bad = await client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": provider_id, "status": "success"},
        headers={"X-Webhook-Signature": bad_sig},
    )
    assert bad.status_code == 400
    assert "Invalid webhook signature" in bad.json()["detail"]

    good_sig = hmac_mod.new(secret.encode(), f"{provider_id}:success".encode(), hashlib_mod.sha256).hexdigest()
    good = await client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": provider_id, "status": "success"},
        headers={"X-Webhook-Signature": good_sig},
    )
    assert good.status_code == 200

    missing = await client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": provider_id, "status": "failed"},
    )
    assert missing.status_code == 400
    assert "Missing webhook signature" in missing.json()["detail"]
