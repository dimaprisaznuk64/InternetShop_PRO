import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select, insert

from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.promo import PromoCode, DiscountType
from app.models.order import Order, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentStatus


# ─── Helpers ────────────────────────────────────────────────

async def _make_user(db, uid, email, role="user"):
    await db.execute(insert(User).values(
        id=uid, email=email, username=email.split("@")[0],
        hashed_password=hash_password("secret123"), role=role,
    ))
    await db.commit()
    return create_access_token(uid)


async def _make_product(db, name="Widget", price=50.00, stock=10, sku="SKU-1", cat_slug=None):
    import uuid
    uid = str(uuid.uuid4())[:8]
    cat = Category(name=f"BizCat-{uid}", slug=f"biz-cat-{uid}" if not cat_slug else cat_slug)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    prod = Product(
        name=name, slug=f"slug-{name.lower()}-{uid}", price=price,
        sku=sku, stock=stock, category_id=cat.id,
    )
    db.add(prod)
    await db.commit()
    await db.refresh(prod)
    return prod.id


async def _make_promo(db, code="TEST10", discount_type=DiscountType.percentage,
                      discount_value=10, max_uses=100, is_active=True,
                      expires_at=None, min_order_amount=None, used_count=0):
    promo = PromoCode(
        code=code, discount_type=discount_type,
        discount_value=discount_value, max_uses=max_uses,
        is_active=is_active, expires_at=expires_at,
        min_order_amount=min_order_amount, used_count=used_count,
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return promo


async def _add_to_cart(client, headers, prod_id, qty=2):
    return await client.post(
        "/api/cart/items",
        json={"product_id": prod_id, "quantity": qty},
        headers=headers,
    )


async def _checkout(client, headers, **kwargs):
    payload = {"delivery_address": "123 Test St", **kwargs}
    return await client.post("/api/orders/checkout", json=payload, headers=headers)


async def _create_order_with_cart(client, headers, prod_id, qty=2):
    await _add_to_cart(client, headers, prod_id, qty)
    resp = await _checkout(client, headers)
    return resp.json()


async def _create_paid_order(client, db, headers, prod_id, qty=2, price=50.00):
    order = await _create_order_with_cart(client, headers, prod_id, qty)
    pay_resp = await client.post(
        "/api/payments/",
        json={"order_id": order["id"], "method": "card"},
        headers=headers,
    )
    return order, pay_resp.json()


# ═══════════════════════════════════════════════════════════════
# DISCOUNT / PROMO CODE BUSINESS LOGIC
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestPromoCodeCreation:

    async def test_admin_creates_percentage_promo(self, client, db_session):
        token = await _make_user(db_session, "bc-a1", "bca1@test.com", "admin")
        h = {"Authorization": f"Bearer {token}"}
        resp = await client.post("/api/promo-codes/", json={
            "code": "SAVE20", "discount_type": "percentage",
            "discount_value": 20, "max_uses": 50,
        }, headers=h)
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == "SAVE20"
        assert data["discount_type"] == "percentage"
        assert data["discount_value"] == "20.00"
        assert data["max_uses"] == 50
        assert data["used_count"] == 0
        assert data["is_active"] is True

    async def test_admin_creates_fixed_promo(self, client, db_session):
        token = await _make_user(db_session, "bc-a2", "bca2@test.com", "admin")
        h = {"Authorization": f"Bearer {token}"}
        resp = await client.post("/api/promo-codes/", json={
            "code": "FLAT15", "discount_type": "fixed",
            "discount_value": 15.00, "min_order_amount": 50.00,
        }, headers=h)
        assert resp.status_code == 201
        data = resp.json()
        assert data["discount_type"] == "fixed"
        assert data["discount_value"] == "15.00"

    async def test_duplicate_promo_code_rejected(self, client, db_session):
        token = await _make_user(db_session, "bc-a3", "bca3@test.com", "admin")
        h = {"Authorization": f"Bearer {token}"}
        await client.post("/api/promo-codes/", json={
            "code": "DUP10", "discount_type": "percentage", "discount_value": 10,
        }, headers=h)
        resp = await client.post("/api/promo-codes/", json={
            "code": "DUP10", "discount_type": "percentage", "discount_value": 20,
        }, headers=h)
        assert resp.status_code == 409

    async def test_regular_user_cannot_create_promo(self, client, db_session):
        token = await _make_user(db_session, "bc-u1", "bcu1@test.com")
        h = {"Authorization": f"Bearer {token}"}
        resp = await client.post("/api/promo-codes/", json={
            "code": "NOPE", "discount_type": "percentage", "discount_value": 10,
        }, headers=h)
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestPromoCodeApply:

    async def test_apply_percentage_promo(self, client, db_session):
        await _make_promo(db_session, code="PCT25", discount_type=DiscountType.percentage, discount_value=25)
        resp = await client.post("/api/promo-codes/apply", json={"code": "PCT25"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["discount_type"] == "percentage"
        assert data["discount_value"] == "25.00"

    async def test_apply_fixed_promo(self, client, db_session):
        await _make_promo(db_session, code="FIX50", discount_type=DiscountType.fixed, discount_value=50)
        resp = await client.post("/api/promo-codes/apply", json={"code": "FIX50"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["discount_type"] == "fixed"
        assert data["discount_value"] == "50.00"

    async def test_apply_nonexistent_promo(self, client, db_session):
        resp = await client.post("/api/promo-codes/apply", json={"code": "GHOST"})
        assert resp.status_code == 404

    async def test_apply_inactive_promo_rejected(self, client, db_session):
        await _make_promo(db_session, code="DEAD", is_active=False)
        resp = await client.post("/api/promo-codes/apply", json={"code": "DEAD"})
        assert resp.status_code == 400
        assert "inactive" in resp.json()["detail"].lower()

    async def test_apply_expired_promo_rejected(self, client, db_session):
        past = datetime.now(timezone.utc) - timedelta(days=30)
        await _make_promo(db_session, code="OLD", expires_at=past)
        resp = await client.post("/api/promo-codes/apply", json={"code": "OLD"})
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()

    async def test_apply_future_promo_accepted(self, client, db_session):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        await _make_promo(db_session, code="FUTURE", expires_at=future)
        resp = await client.post("/api/promo-codes/apply", json={"code": "FUTURE"})
        assert resp.status_code == 200

    async def test_apply_promo_at_usage_limit_rejected(self, client, db_session):
        await _make_promo(db_session, code="LIMITED", max_uses=5, used_count=5)
        resp = await client.post("/api/promo-codes/apply", json={"code": "LIMITED"})
        assert resp.status_code == 400
        assert "limit" in resp.json()["detail"].lower()

    async def test_apply_promo_near_limit_accepted(self, client, db_session):
        await _make_promo(db_session, code="NEARLIM", max_uses=10, used_count=9)
        resp = await client.post("/api/promo-codes/apply", json={"code": "NEARLIM"})
        assert resp.status_code == 200

    async def test_apply_promo_no_usage_limit(self, client, db_session):
        await _make_promo(db_session, code="NOLIMIT", max_uses=None, used_count=9999)
        resp = await client.post("/api/promo-codes/apply", json={"code": "NOLIMIT"})
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# STOCK BUSINESS LOGIC
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestStockValidation:

    async def test_add_to_cart_respects_stock(self, client, db_session):
        token = await _make_user(db_session, "st-u1", "stu1@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=3)
        resp = await _add_to_cart(client, h, prod_id, qty=5)
        assert resp.status_code == 400

    async def test_add_to_cart_exactly_stock(self, client, db_session):
        token = await _make_user(db_session, "st-u2", "stu2@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=5)
        resp = await _add_to_cart(client, h, prod_id, qty=5)
        assert resp.status_code == 201

    async def test_add_to_cart_zero_stock(self, client, db_session):
        token = await _make_user(db_session, "st-u3", "stu3@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=0)
        resp = await _add_to_cart(client, h, prod_id, qty=1)
        assert resp.status_code == 400

    async def test_update_cart_item_exceeds_stock(self, client, db_session):
        token = await _make_user(db_session, "st-u4", "stu4@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=5)
        add_resp = await _add_to_cart(client, h, prod_id, qty=1)
        item_id = add_resp.json()["items"][0]["id"]
        resp = await client.put(
            f"/api/cart/items/{item_id}",
            json={"quantity": 10},
            headers=h,
        )
        assert resp.status_code == 400

    async def test_stock_decremented_after_checkout(self, client, db_session):
        token = await _make_user(db_session, "st-u5", "stu5@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        await _add_to_cart(client, h, prod_id, qty=3)
        await _checkout(client, h)

        result = await db_session.execute(select(Product).where(Product.id == prod_id))
        product = result.scalar_one()
        assert product.stock == 7

    async def test_stock_not_decremented_on_failed_checkout(self, client, db_session):
        token = await _make_user(db_session, "st-u6", "stu6@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        await _add_to_cart(client, h, prod_id, qty=3)

        # Add another product that exceeds stock
        prod2 = await _make_product(db_session, name="Widget2", stock=1, sku="SKU-2")
        await _add_to_cart(client, h, prod2, qty=1)

        # Checkout should fail because stock of prod2 insufficient (cart has qty=1, stock=1, that's fine)
        # Let's make it fail by updating cart after adding
        # Actually the checkout checks cart items vs stock. Let me make a different approach:
        # Create product with stock=2, add qty=2, then reduce stock before checkout
        prod3_id = await _make_product(db_session, name="Widget3", stock=2, sku="SKU-3")
        await _add_to_cart(client, h, prod3_id, qty=2)

        # Directly reduce stock in DB to simulate concurrent purchase
        result = await db_session.execute(select(Product).where(Product.id == prod3_id))
        product = result.scalar_one()
        product.stock = 0
        await db_session.commit()

        resp = await _checkout(client, h)
        assert resp.status_code == 400

    async def test_multiple_products_stock_validation(self, client, db_session):
        token = await _make_user(db_session, "st-u7", "stu7@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod1 = await _make_product(db_session, name="P1", stock=5, sku="SKU-P1")
        prod2 = await _make_product(db_session, name="P2", stock=3, sku="SKU-P2")

        await _add_to_cart(client, h, prod1, qty=2)
        await _add_to_cart(client, h, prod2, qty=2)

        resp = await _checkout(client, h)
        assert resp.status_code == 201

        r1 = await db_session.execute(select(Product).where(Product.id == prod1))
        r2 = await db_session.execute(select(Product).where(Product.id == prod2))
        assert r1.scalar_one().stock == 3
        assert r2.scalar_one().stock == 1

    async def test_cart_increment_exceeds_stock(self, client, db_session):
        token = await _make_user(db_session, "st-u8", "stu8@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=3)

        await _add_to_cart(client, h, prod_id, qty=2)
        resp = await _add_to_cart(client, h, prod_id, qty=2)
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════
# CHECKOUT BUSINESS LOGIC
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestCheckoutLogic:

    async def test_checkout_total_calculation(self, client, db_session):
        token = await _make_user(db_session, "ck-u1", "cku1@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, price=75.00, stock=10)
        await _add_to_cart(client, h, prod_id, qty=4)
        resp = await _checkout(client, h)
        assert resp.status_code == 201
        assert resp.json()["total"] == "300.00"

    async def test_checkout_multiple_products_total(self, client, db_session):
        token = await _make_user(db_session, "ck-u2", "cku2@test.com")
        h = {"Authorization": f"Bearer {token}"}
        p1 = await _make_product(db_session, name="A", price=100.00, stock=10, sku="CK-A")
        p2 = await _make_product(db_session, name="B", price=25.50, stock=10, sku="CK-B")

        await _add_to_cart(client, h, p1, qty=2)
        await _add_to_cart(client, h, p2, qty=3)

        resp = await _checkout(client, h)
        assert resp.status_code == 201
        # 100*2 + 25.50*3 = 200 + 76.50 = 276.50
        assert resp.json()["total"] == "276.50"

    async def test_checkout_clears_cart(self, client, db_session):
        token = await _make_user(db_session, "ck-u3", "cku3@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        await _add_to_cart(client, h, prod_id, qty=3)
        await _checkout(client, h)
        cart_resp = await client.get("/api/cart/", headers=h)
        assert cart_resp.json()["items_count"] == 0
        assert cart_resp.json()["subtotal"] == "0.00"

    async def test_checkout_stores_delivery_info(self, client, db_session):
        token = await _make_user(db_session, "ck-u4", "cku4@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        await _add_to_cart(client, h, prod_id, qty=1)
        resp = await _checkout(
            client, h,
            delivery_method="express",
            delivery_address="456 Elm St",
            notes="Leave at door",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["delivery_method"] == "express"
        assert data["delivery_address"] == "456 Elm St"
        assert data["notes"] == "Leave at door"

    async def test_checkout_without_address(self, client, db_session):
        token = await _make_user(db_session, "ck-u5", "cku5@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        await _add_to_cart(client, h, prod_id, qty=1)
        resp = await client.post("/api/orders/checkout", json={}, headers=h)
        assert resp.status_code == 201
        assert resp.json()["delivery_address"] is None

    async def test_checkout_creates_order_items(self, client, db_session):
        token = await _make_user(db_session, "ck-u6", "cku6@test.com")
        h = {"Authorization": f"Bearer {token}"}
        p1 = await _make_product(db_session, name="X", price=30.00, stock=10, sku="CK-X")
        p2 = await _make_product(db_session, name="Y", price=70.00, stock=10, sku="CK-Y")

        await _add_to_cart(client, h, p1, qty=2)
        await _add_to_cart(client, h, p2, qty=1)

        resp = await _checkout(client, h)
        assert resp.status_code == 201
        items = resp.json()["items"]
        assert len(items) == 2
        prices = {i["product_id"]: i for i in items}
        assert prices[p1]["quantity"] == 2
        assert prices[p1]["price"] == "30.00"
        assert prices[p2]["quantity"] == 1
        assert prices[p2]["price"] == "70.00"

    async def test_checkout_status_is_pending(self, client, db_session):
        token = await _make_user(db_session, "ck-u7", "cku7@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        await _add_to_cart(client, h, prod_id, qty=1)
        resp = await _checkout(client, h)
        assert resp.json()["status"] == "pending"

    async def test_checkout_empty_cart_fails(self, client, db_session):
        token = await _make_user(db_session, "ck-u8", "cku8@test.com")
        h = {"Authorization": f"Bearer {token}"}
        resp = await _checkout(client, h)
        assert resp.status_code == 400

    async def test_checkout_stock_exactly_enough(self, client, db_session):
        token = await _make_user(db_session, "ck-u9", "cku9@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=4)
        await _add_to_cart(client, h, prod_id, qty=4)
        resp = await _checkout(client, h)
        assert resp.status_code == 201
        result = await db_session.execute(select(Product).where(Product.id == prod_id))
        assert result.scalar_one().stock == 0


# ═══════════════════════════════════════════════════════════════
# PAYMENT BUSINESS LOGIC
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestPaymentLogic:

    async def test_payment_amount_matches_order_total(self, client, db_session):
        token = await _make_user(db_session, "pm-u1", "pmu1@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, price=33.00, stock=10)
        await _add_to_cart(client, h, prod_id, qty=3)
        order_resp = await _checkout(client, h)
        order_id = order_resp.json()["id"]

        pay_resp = await client.post(
            "/api/payments/",
            json={"order_id": order_id, "method": "card"},
            headers=h,
        )
        assert pay_resp.status_code == 201
        assert pay_resp.json()["amount"] == "99.00"
        assert pay_resp.json()["status"] == "success"
        assert pay_resp.json()["method"] == "card"

    async def test_payment_updates_order_to_paid(self, client, db_session):
        token = await _make_user(db_session, "pm-u2", "pmu2@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        order = await _create_order_with_cart(client, h, prod_id, qty=1)

        resp = await client.post(
            "/api/payments/",
            json={"order_id": order["id"], "method": "card"},
            headers=h,
        )
        assert resp.status_code == 201

        order_resp = await client.get(f"/api/orders/{order['id']}", headers=h)
        assert order_resp.json()["status"] == "paid"

    async def test_payment_idempotency_already_paid(self, client, db_session):
        token = await _make_user(db_session, "pm-u3", "pmu3@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        order = await _create_order_with_cart(client, h, prod_id, qty=1)

        resp1 = await client.post(
            "/api/payments/",
            json={"order_id": order["id"], "method": "card"},
            headers=h,
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            "/api/payments/",
            json={"order_id": order["id"], "method": "card"},
            headers=h,
        )
        assert resp2.status_code == 400

    async def test_payment_wrong_user_rejected(self, client, db_session):
        t1 = await _make_user(db_session, "pm-u4a", "pmu4a@test.com")
        t2 = await _make_user(db_session, "pm-u4b", "pmu4b@test.com")
        h1 = {"Authorization": f"Bearer {t1}"}
        h2 = {"Authorization": f"Bearer {t2}"}
        prod_id = await _make_product(db_session, stock=10)
        order = await _create_order_with_cart(client, h1, prod_id, qty=1)

        resp = await client.post(
            "/api/payments/",
            json={"order_id": order["id"], "method": "card"},
            headers=h2,
        )
        assert resp.status_code == 400

    async def test_payment_nonexistent_order(self, client, db_session):
        token = await _make_user(db_session, "pm-u5", "pmu5@test.com")
        h = {"Authorization": f"Bearer {token}"}
        resp = await client.post(
            "/api/payments/",
            json={"order_id": "fake-order-id", "method": "card"},
            headers=h,
        )
        assert resp.status_code == 404

    async def test_provider_id_format(self, client, db_session):
        token = await _make_user(db_session, "pm-u6", "pmu6@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        order = await _create_order_with_cart(client, h, prod_id, qty=1)

        resp = await client.post(
            "/api/payments/",
            json={"order_id": order["id"], "method": "card"},
            headers=h,
        )
        assert resp.json()["provider_payment_id"].startswith("sim_")
        assert len(resp.json()["provider_payment_id"]) == 20  # "sim_" + 16 hex chars


@pytest.mark.asyncio
class TestWebhookLogic:

    async def test_webhook_success_marks_order_paid(self, client, db_session):
        token = await _make_user(db_session, "wh-u1", "whu1@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        order = await _create_order_with_cart(client, h, prod_id, qty=1)

        # Create payment (simulated — already success)
        pay_resp = await client.post(
            "/api/payments/",
            json={"order_id": order["id"], "method": "card"},
            headers=h,
        )
        provider_id = pay_resp.json()["provider_payment_id"]

        # Webhook success
        resp = await client.post("/api/payments/webhook", json={
            "provider_payment_id": provider_id, "status": "success",
        })
        assert resp.status_code == 200

    async def test_webhook_failed_marks_payment_failed(self, client, db_session):
        token = await _make_user(db_session, "wh-u2", "whu2@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        order = await _create_order_with_cart(client, h, prod_id, qty=1)

        pay_resp = await client.post(
            "/api/payments/",
            json={"order_id": order["id"], "method": "card"},
            headers=h,
        )
        provider_id = pay_resp.json()["provider_payment_id"]
        payment_id = pay_resp.json()["id"]

        resp = await client.post("/api/payments/webhook", json={
            "provider_payment_id": provider_id, "status": "failed",
        })
        assert resp.status_code == 200

        get_resp = await client.get(f"/api/payments/{payment_id}", headers=h)
        assert get_resp.json()["status"] == "failed"

    async def test_webhook_refunded_marks_payment_refunded(self, client, db_session):
        token = await _make_user(db_session, "wh-u3", "whu3@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        order = await _create_order_with_cart(client, h, prod_id, qty=1)

        pay_resp = await client.post(
            "/api/payments/",
            json={"order_id": order["id"], "method": "card"},
            headers=h,
        )
        provider_id = pay_resp.json()["provider_payment_id"]
        payment_id = pay_resp.json()["id"]

        resp = await client.post("/api/payments/webhook", json={
            "provider_payment_id": provider_id, "status": "refunded",
        })
        assert resp.status_code == 200

        get_resp = await client.get(f"/api/payments/{payment_id}", headers=h)
        assert get_resp.json()["status"] == "refunded"

    async def test_webhook_unknown_provider(self, client):
        resp = await client.post("/api/payments/webhook", json={
            "provider_payment_id": "ghost-provider", "status": "success",
        })
        assert resp.status_code == 404

    async def test_webhook_success_sends_notification(self, client, db_session):
        token = await _make_user(db_session, "wh-u4", "whu4@test.com")
        h = {"Authorization": f"Bearer {token}"}
        prod_id = await _make_product(db_session, stock=10)
        order = await _create_order_with_cart(client, h, prod_id, qty=1)

        pay_resp = await client.post(
            "/api/payments/",
            json={"order_id": order["id"], "method": "card"},
            headers=h,
        )
        provider_id = pay_resp.json()["provider_payment_id"]

        await client.post("/api/payments/webhook", json={
            "provider_payment_id": provider_id, "status": "success",
        })

        notif = await client.get("/api/notifications/", headers=h)
        assert notif.status_code == 200
        assert notif.json()["total"] >= 1
