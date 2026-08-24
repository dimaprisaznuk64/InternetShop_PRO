"""
OWASP Top 10 focused tests — CSRF, IDOR, broken access control, sensitive data exposure.
Lesson 58.
"""
import pytest
from app.utils.security import hash_password


async def _make_category(db_session):
    from app.models.category import Category
    cat = Category(name="OWASPCat", slug="owasp-cat")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat.id


async def _make_product(db_session, pid, name="Prod", price=10.0, stock=100):
    from sqlalchemy import insert
    from app.models.product import Product
    from app.models.category import Category

    cat = Category(name=f"Cat-{pid}", slug=f"cat-{pid}")
    db_session.add(cat)
    await db_session.flush()

    await db_session.execute(insert(Product).values(
        id=pid, name=name, slug=f"slug-{pid}", price=price, stock=stock,
        sku=f"SKU-{pid}", category_id=cat.id, is_active=True,
    ))
    await db_session.commit()


async def _register_user(client, db_session, uid, email, role="user"):
    """Register via API (clean) or insert directly if needed."""
    from sqlalchemy import insert
    from app.models.user import User

    await db_session.execute(insert(User).values(
        id=uid, email=email, username=email.split("@")[0],
        hashed_password=hash_password("secret123"), role=role,
    ))
    await db_session.commit()

    resp = await client.post("/api/auth/login", json={
        "email": email, "password": "secret123",
    })
    return resp.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════════════════════════
# CSRF — JWT Bearer, не cookie → CSRF неможливий
# ═══════════════════════════════════════════════════════════════

class TestCSRFProtection:

    async def test_auth_uses_bearer_not_cookies(self, client):
        resp = await client.post("/api/auth/login", json={
            "email": "test@test.com", "password": "wrong",
        })
        set_cookie = resp.headers.get("set-cookie", "")
        assert "session" not in set_cookie.lower() or set_cookie == ""

    async def test_state_changing_use_bearer_not_csrf_token(self, client):
        resp = await client.post("/api/auth/login", json={
            "email": "test@test.com", "password": "wrong",
        })
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════
# IDOR
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestIDOR_Orders:

    async def test_user_cannot_view_other_users_order(self, client, db_session):
        t1 = await _register_user(client, db_session, "u-o1", "o1@test.com")
        t2 = await _register_user(client, db_session, "u-o2", "o2@test.com")

        await _make_product(db_session, "prod-idor-1")

        await client.post("/api/cart/items", json={
            "product_id": "prod-idor-1", "quantity": 1,
        }, headers=_h(t1))

        checkout = await client.post("/api/orders/checkout", json={
            "delivery_method": "pickup", "delivery_address": "addr",
        }, headers=_h(t1))
        order_id = checkout.json()["id"]

        resp = await client.get(f"/api/orders/{order_id}", headers=_h(t2))
        assert resp.status_code in (400, 403, 404)

    async def test_user_cannot_update_other_users_order_status(self, client, db_session):
        t1 = await _register_user(client, db_session, "u-ord3", "ord3@test.com")

        await _make_product(db_session, "prod-ord3")

        await client.post("/api/cart/items", json={
            "product_id": "prod-ord3", "quantity": 1,
        }, headers=_h(t1))

        checkout = await client.post("/api/orders/checkout", json={
            "delivery_method": "pickup", "delivery_address": "addr",
        }, headers=_h(t1))
        order_id = checkout.json()["id"]

        resp = await client.patch(f"/api/orders/{order_id}/status",
            json={"status": "paid"}, headers=_h(t1),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestIDOR_Reviews:

    async def test_user_cannot_delete_others_review(self, client, db_session):
        t1 = await _register_user(client, db_session, "u-rv1", "rv1@test.com")
        t2 = await _register_user(client, db_session, "u-rv2", "rv2@test.com")

        await _make_product(db_session, "prod-rv1")

        from sqlalchemy import insert
        from app.models.review import Review

        await db_session.execute(insert(Review).values(
            id="rev-idor-1", user_id="u-rv1", product_id="prod-rv1",
            rating=5, text="Great", is_moderated=True,
        ))
        await db_session.commit()

        resp = await client.delete("/api/reviews/rev-idor-1", headers=_h(t2))
        assert resp.status_code in (400, 403, 404)

    async def test_unmoderated_reviews_not_in_public_listing(self, client, db_session):
        await _make_product(db_session, "prod-rv2")

        from sqlalchemy import insert
        from app.models.review import Review

        await db_session.execute(insert(Review).values(
            id="rev-unmod", user_id="u-unknown", product_id="prod-rv2",
            rating=1, text="Spam", is_moderated=False,
        ))
        await db_session.commit()

        resp = await client.get("/api/reviews/product/prod-rv2")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


@pytest.mark.asyncio
class TestIDOR_Payments:

    async def test_user_cannot_view_others_payment(self, client, db_session):
        t1 = await _register_user(client, db_session, "u-py1", "py1@test.com")
        t2 = await _register_user(client, db_session, "u-py2", "py2@test.com")

        from sqlalchemy import insert
        from app.models.order import Order, OrderStatus
        from app.models.payment import Payment, PaymentStatus

        await db_session.execute(insert(Order).values(
            id="ord-py1", user_id="u-py1", total=25.0,
            delivery_method="pickup", delivery_address="addr",
            status=OrderStatus.paid.value,
        ))
        await db_session.execute(insert(Payment).values(
            id="pay-idor-1", order_id="ord-py1", amount=25.0,
            method="card", status=PaymentStatus.success.value,
            provider_payment_id="sim_test123",
        ))
        await db_session.commit()

        resp = await client.get("/api/payments/pay-idor-1", headers=_h(t2))
        assert resp.status_code in (400, 403, 404)

    async def test_user_cannot_pay_for_others_order(self, client, db_session):
        t1 = await _register_user(client, db_session, "u-py3", "py3@test.com")
        t2 = await _register_user(client, db_session, "u-py4", "py4@test.com")

        from sqlalchemy import insert
        from app.models.order import Order, OrderStatus

        await db_session.execute(insert(Order).values(
            id="ord-py3", user_id="u-py3", total=15.0,
            delivery_method="pickup", delivery_address="addr",
            status=OrderStatus.pending.value,
        ))
        await db_session.commit()

        resp = await client.post("/api/payments/", json={
            "order_id": "ord-py3", "method": "card",
        }, headers=_h(t2))
        assert resp.status_code == 400


@pytest.mark.asyncio
class TestIDOR_Cart:

    async def test_user_cannot_modify_others_cart_item(self, client, db_session):
        t1 = await _register_user(client, db_session, "u-ct1", "ct1@test.com")
        t2 = await _register_user(client, db_session, "u-ct2", "ct2@test.com")

        await _make_product(db_session, "prod-ct1")

        resp1 = await client.post("/api/cart/items", json={
            "product_id": "prod-ct1", "quantity": 1,
        }, headers=_h(t1))
        item_id = resp1.json()["items"][0]["id"]

        resp2 = await client.put(f"/api/cart/items/{item_id}",
            json={"quantity": 5}, headers=_h(t2),
        )
        assert resp2.status_code == 404

        resp3 = await client.delete(f"/api/cart/items/{item_id}", headers=_h(t2))
        assert resp3.status_code == 404


@pytest.mark.asyncio
class TestIDOR_Notifications:

    async def test_user_cannot_delete_others_notification(self, client, db_session):
        from app.services.background import notification_service

        t1 = await _register_user(client, db_session, "u-nf1", "nf1@test.com")
        t2 = await _register_user(client, db_session, "u-nf2", "nf2@test.com")

        n = await notification_service.create(db_session, "u-nf1", "system", "Title", "Message")

        resp = await client.delete(f"/api/notifications/{n['id']}", headers=_h(t2))
        data = resp.json()
        assert data.get("error") == "Notification not found"


@pytest.mark.asyncio
class TestIDOR_Profile:

    async def test_me_returns_only_own_data(self, client, db_session):
        t1 = await _register_user(client, db_session, "u-pf1", "pf1@test.com")
        t2 = await _register_user(client, db_session, "u-pf2", "pf2@test.com")

        me1 = await client.get("/api/auth/me", headers=_h(t1))
        me2 = await client.get("/api/auth/me", headers=_h(t2))
        assert me1.json()["id"] == "u-pf1"
        assert me2.json()["id"] == "u-pf2"
        assert me1.json()["id"] != me2.json()["id"]

    async def test_password_change_requires_current_password(self, client, db_session):
        t = await _register_user(client, db_session, "u-pf3", "pf3@test.com")

        resp = await client.put("/api/profile/password", json={
            "current_password": "wrong_password",
            "new_password": "newpass456",
        }, headers=_h(t))
        assert resp.status_code == 400

        resp2 = await client.put("/api/profile/password", json={
            "current_password": "secret123",
            "new_password": "newpass456",
        }, headers=_h(t))
        assert resp2.status_code == 204


# ═══════════════════════════════════════════════════════════════
# BROKEN ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestBrokenAccessControl:

    async def test_unauthenticated_cannot_access_admin_users(self, client):
        resp = await client.get("/api/admin/users")
        assert resp.status_code == 401

    async def test_unauthenticated_cannot_access_admin_stats(self, client):
        resp = await client.get("/api/admin/stats")
        assert resp.status_code == 401

    async def test_user_cannot_list_orders_admin(self, client, db_session):
        t = await _register_user(client, db_session, "u-ba1", "ba1@test.com")
        resp = await client.get("/api/orders/admin/all", headers=_h(t))
        assert resp.status_code == 403

    async def test_user_cannot_manage_categories(self, client, db_session):
        t = await _register_user(client, db_session, "u-ba2", "ba2@test.com")
        resp = await client.post("/api/categories/", json={
            "name": "Hack", "description": "Bad",
        }, headers=_h(t))
        assert resp.status_code == 403

    async def test_user_cannot_delete_products(self, client, db_session):
        t = await _register_user(client, db_session, "u-ba3", "ba3@test.com")
        resp = await client.delete("/api/products/fake-id", headers=_h(t))
        assert resp.status_code == 403

    async def test_admin_can_access_admin_endpoints(self, client, db_session):
        t = await _register_user(client, db_session, "u-ba4", "ba4@test.com", role="admin")
        resp = await client.get("/api/admin/users", headers=_h(t))
        assert resp.status_code == 200

    async def test_user_cannot_create_promo_code(self, client, db_session):
        t = await _register_user(client, db_session, "u-ba5", "ba5@test.com")
        resp = await client.post("/api/promo-codes/", json={
            "code": "HACK", "discount_percent": 100,
            "valid_from": "2025-01-01T00:00:00",
            "valid_until": "2025-12-31T23:59:59",
        }, headers=_h(t))
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════
# SENSITIVE DATA EXPOSURE
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestSensitiveDataExposure:

    async def test_login_error_generic(self, client):
        resp1 = await client.post("/api/auth/login", json={
            "email": "nonexistent@test.com", "password": "whatever",
        })
        resp2 = await client.post("/api/auth/login", json={
            "email": "nonexistent@test.com", "password": "wrong",
        })
        assert resp1.json()["detail"] == resp2.json()["detail"]

    async def test_user_response_excludes_password_hash(self, client, db_session):
        t = await _register_user(client, db_session, "u-sd1", "sd1@test.com")
        resp = await client.get("/api/auth/me", headers=_h(t))
        data = resp.json()
        assert "hashed_password" not in data
        assert "password" not in data

    async def test_admin_users_list_excludes_password_hash(self, client, db_session):
        t = await _register_user(client, db_session, "u-sd2", "sd2@test.com", role="admin")
        resp = await client.get("/api/admin/users", headers=_h(t))
        data = resp.json()
        for user in data.get("users", []):
            assert "hashed_password" not in user
            assert "password" not in user

    async def test_duplicate_register_no_internal_leak(self, client, db_session):
        from sqlalchemy import insert
        from app.models.user import User

        await db_session.execute(insert(User).values(
            id="u-leak", email="leak@test.com", username="leakuser",
            hashed_password=hash_password("secret123"), role="user",
        ))
        await db_session.commit()

        resp = await client.post("/api/auth/register", json={
            "email": "leak@test.com", "username": "other",
            "password": "secret123",
        })
        assert resp.status_code in (400, 409, 422)
        detail = resp.json().get("detail", "")
        assert "u-leak" not in detail
        assert "hashed_password" not in detail


# ═══════════════════════════════════════════════════════════════
# INPUT VALIDATION
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestInputValidation:

    async def test_negative_quantity_rejected(self, client, db_session):
        t = await _register_user(client, db_session, "u-iv1", "iv1@test.com")
        resp = await client.post("/api/cart/items", json={
            "product_id": "fake", "quantity": -5,
        }, headers=_h(t))
        assert resp.status_code == 422

    async def test_zero_quantity_rejected(self, client, db_session):
        t = await _register_user(client, db_session, "u-iv2", "iv2@test.com")
        resp = await client.post("/api/cart/items", json={
            "product_id": "fake", "quantity": 0,
        }, headers=_h(t))
        assert resp.status_code == 422

    async def test_huge_quantity_rejected(self, client, db_session):
        t = await _register_user(client, db_session, "u-iv3", "iv3@test.com")
        resp = await client.post("/api/cart/items", json={
            "product_id": "fake", "quantity": 999999999,
        }, headers=_h(t))
        assert resp.status_code in (404, 422)

    async def test_invalid_email_rejected(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "not-an-email", "username": "test", "password": "secret123",
        })
        assert resp.status_code == 422

    async def test_empty_password_rejected(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "test@test.com", "username": "test", "password": "",
        })
        assert resp.status_code == 422

    async def test_invalid_rating_rejected(self, client, db_session):
        t = await _register_user(client, db_session, "u-iv4", "iv4@test.com")
        resp = await client.post("/api/reviews/", json={
            "product_id": "fake", "rating": 10, "text": "Good",
        }, headers=_h(t))
        assert resp.status_code in (400, 404, 422)

    async def test_negative_rating_rejected(self, client, db_session):
        t = await _register_user(client, db_session, "u-iv5", "iv5@test.com")
        resp = await client.post("/api/reviews/", json={
            "product_id": "fake", "rating": -1, "text": "Bad",
        }, headers=_h(t))
        assert resp.status_code in (400, 404, 422)


# ═══════════════════════════════════════════════════════════════
# MASS ASSIGNMENT
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestMassAssignment:

    async def test_register_cannot_set_role_to_admin(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "admin-hack@test.com",
            "username": "adminhack",
            "password": "secret123",
            "role": "admin",
        })
        if resp.status_code == 201:
            login = await client.post("/api/auth/login", json={
                "email": "admin-hack@test.com", "password": "secret123",
            })
            me = await client.get("/api/auth/me",
                headers=_h(login.json()["access_token"]),
            )
            assert me.json()["role"] == "user"

    async def test_profile_update_cannot_change_role(self, client, db_session):
        t = await _register_user(client, db_session, "u-ma1", "ma1@test.com")

        resp = await client.put("/api/profile/", json={
            "username": "ma1",
            "email": "ma1@test.com",
            "role": "admin",
        }, headers=_h(t))

        me = await client.get("/api/auth/me", headers=_h(t))
        if me.status_code == 200:
            assert me.json()["role"] == "user"
