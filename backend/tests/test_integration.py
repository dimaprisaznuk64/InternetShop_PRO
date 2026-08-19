import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func

from app.utils.security import hash_password
from app.database import AsyncSession
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.promo import PromoCode, DiscountType
from app.models.order import Order, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.review import Review
from app.models.favorite import Favorite


# ─── Helpers ────────────────────────────────────────────────

async def _register(client, email="int@test.com", username="intuser", password="secret123"):
    return await client.post("/api/auth/register", json={
        "email": email, "username": username, "password": password,
    })


async def _login(client, email="int@test.com", password="secret123"):
    return await client.post("/api/auth/login", json={
        "email": email, "password": password,
    })


async def _auth(client, email="int@test.com", password="secret123"):
    resp = await _login(client, email, password)
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _make_admin(client, db, email="adm@test.com"):
    import uuid
    uid = f"intg-admin-{str(uuid.uuid4())[:8]}"
    await db.execute(
        __import__("sqlalchemy").insert(User).values(
            id=uid, email=email, username=email.split("@")[0],
            hashed_password=hash_password("secret123"), role="admin",
        )
    )
    await db.commit()
    return await _auth(client, email)


async def _make_manager(client, db, email="mgr@test.com"):
    import uuid
    uid = f"intg-mgr-{str(uuid.uuid4())[:8]}"
    await db.execute(
        __import__("sqlalchemy").insert(User).values(
            id=uid, email=email, username=email.split("@")[0],
            hashed_password=hash_password("secret123"), role="manager",
        )
    )
    await db.commit()
    return await _auth(client, email)


async def _create_category(client, admin_h, name="Electronics", slug=None):
    import uuid
    s = slug or f"cat-{str(uuid.uuid4())[:8]}"
    resp = await client.post("/api/categories/", json={
        "name": name, "slug": s,
    }, headers=admin_h)
    return resp.json()["id"]


async def _create_product(client, manager_h, cat_id, name="Widget", price=50.00, stock=10, sku=None):
    import uuid
    uid = str(uuid.uuid4())[:8]
    resp = await client.post("/api/products/", json={
        "name": name, "slug": f"slug-{uid}", "sku": sku or f"SKU-{uid}",
        "price": price, "stock": stock, "category_id": cat_id,
        "description": f"Test {name}",
    }, headers=manager_h)
    return resp.json()["id"]


async def _add_cart(client, h, prod_id, qty=2):
    return await client.post("/api/cart/items",
        json={"product_id": prod_id, "quantity": qty}, headers=h)


async def _checkout(client, h, **kw):
    payload = {"delivery_address": "123 Main St", **kw}
    return await client.post("/api/orders/checkout", json=payload, headers=h)


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TEST 1: Full Auth Lifecycle
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestAuthLifecycle:

    async def test_register_login_profile_me(self, client, db_session):
        resp = await _register(client, email="life@test.com", username="lifeuser")
        assert resp.status_code == 201
        user = resp.json()
        assert user["email"] == "life@test.com"
        assert user["username"] == "lifeuser"
        assert user["role"] == "user"

        h = await _auth(client, "life@test.com")
        me = await client.get("/api/auth/me", headers=h)
        assert me.status_code == 200
        assert me.json()["id"] == user["id"]

    async def test_login_wrong_password(self, client, db_session):
        await _register(client, email="wrong@test.com", username="wronguser")
        resp = await _login(client, "wrong@test.com", "badpassword")
        assert resp.status_code == 400

    async def test_register_duplicate_email(self, client, db_session):
        await _register(client, email="dup@test.com", username="dup1")
        resp = await _register(client, email="dup@test.com", username="dup2")
        assert resp.status_code == 409

    async def test_profile_update_and_password_change(self, client, db_session):
        await _register(client, email="prof@test.com", username="profuser")
        h = await _auth(client, "prof@test.com")

        update = await client.put("/api/profile/", json={
            "username": "updated_name", "email": "prof@test.com",
        }, headers=h)
        assert update.status_code == 200
        assert update.json()["username"] == "updated_name"

        pwd = await client.put("/api/profile/password", json={
            "current_password": "secret123", "new_password": "newpass456",
        }, headers=h)
        assert pwd.status_code == 204

        h2 = await _auth(client, "prof@test.com", "newpass456")
        me = await client.get("/api/auth/me", headers=h2)
        assert me.status_code == 200

    async def test_refresh_token(self, client, db_session):
        await _register(client, email="refresh@test.com", username="refuser")
        login_resp = await _login(client, "refresh@test.com")
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert "refresh_token" in resp.json()

    async def test_profile_delete(self, client, db_session):
        await _register(client, email="del@test.com", username="deluser")
        h = await _auth(client, "del@test.com")

        resp = await client.delete("/api/profile/", headers=h)
        assert resp.status_code == 204

        me = await client.get("/api/auth/me", headers=h)
        assert me.status_code == 401


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TEST 2: Catalog (Category → Product → Search)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestCatalogFlow:

    async def test_category_crud(self, client, db_session):
        ah = await _make_admin(client, db_session)

        create = await client.post("/api/categories/", json={
            "name": "Books", "slug": "books",
        }, headers=ah)
        assert create.status_code == 201
        cat_id = create.json()["id"]

        get = await client.get(f"/api/categories/{cat_id}")
        assert get.status_code == 200
        assert get.json()["name"] == "Books"

        update = await client.put(f"/api/categories/{cat_id}", json={
            "name": "E-Books", "slug": "ebooks",
        }, headers=ah)
        assert update.status_code == 200
        assert update.json()["name"] == "E-Books"

        list_resp = await client.get("/api/categories/")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        delete = await client.delete(f"/api/categories/{cat_id}", headers=ah)
        assert delete.status_code == 204

        get_after = await client.get(f"/api/categories/{cat_id}")
        assert get_after.status_code == 404

    async def test_product_crud_via_manager(self, client, db_session):
        ah = await _make_admin(client, db_session, "crudadmin@test.com")
        mh = await _make_manager(client, db_session, "crudmgr@test.com")

        cat_id = await _create_category(client, ah, slug="crud-cat")

        create = await client.post("/api/products/", json={
            "name": "Laptop", "slug": "laptop", "sku": "LAP-001",
            "price": 999.99, "stock": 25, "category_id": cat_id,
            "description": "Gaming laptop",
        }, headers=mh)
        assert create.status_code == 201
        prod_id = create.json()["id"]

        get = await client.get(f"/api/products/{prod_id}")
        assert get.status_code == 200
        assert get.json()["name"] == "Laptop"
        assert get.json()["price"] == "999.99"

        update = await client.put(f"/api/products/{prod_id}", json={
            "name": "Laptop Pro", "slug": "laptop-pro", "sku": "LAP-002",
            "price": 1299.99, "stock": 15, "category_id": cat_id,
            "description": "Pro gaming laptop",
        }, headers=mh)
        assert update.status_code == 200
        assert update.json()["name"] == "Laptop Pro"

        delete = await client.delete(f"/api/products/{prod_id}", headers=ah)
        assert delete.status_code == 204

    async def test_regular_user_cannot_create_product(self, client, db_session):
        await _register(client, email="regular@test.com", username="regular")
        h = await _auth(client, "regular@test.com")
        ah = await _make_admin(client, db_session, "regadmin@test.com")
        cat_id = await _create_category(client, ah, slug="reg-cat")

        resp = await client.post("/api/products/", json={
            "name": "X", "slug": "x", "sku": "X-1",
            "price": 10, "stock": 1, "category_id": cat_id,
        }, headers=h)
        assert resp.status_code == 403

    async def test_search_and_filter_products(self, client, db_session):
        ah = await _make_admin(client, db_session, "srchadmin@test.com")
        mh = await _make_manager(client, db_session, "srchmgr@test.com")

        cat_id = await _create_category(client, ah, slug="srch-cat")

        await client.post("/api/products/", json={
            "name": "iPhone 15", "slug": "iphone15", "sku": "IPH-15",
            "price": 999.00, "stock": 50, "category_id": cat_id, "brand": "Apple",
        }, headers=mh)
        await client.post("/api/products/", json={
            "name": "Galaxy S24", "slug": "galaxy-s24", "sku": "GAL-24",
            "price": 899.00, "stock": 30, "category_id": cat_id, "brand": "Samsung",
        }, headers=mh)
        await client.post("/api/products/", json={
            "name": "iPad Air", "slug": "ipad-air", "sku": "IPAD-AIR",
            "price": 599.00, "stock": 0, "category_id": cat_id, "brand": "Apple",
        }, headers=mh)

        search = await client.get("/api/products/", params={"q": "iPhone"})
        assert search.status_code == 200
        assert search.json()["total"] == 1
        assert search.json()["products"][0]["name"] == "iPhone 15"

        in_stock = await client.get("/api/products/", params={"in_stock": True})
        assert in_stock.status_code == 200
        names = [p["name"] for p in in_stock.json()["products"]]
        assert "iPad Air" not in names

        brand = await client.get("/api/products/", params={"brand": "Samsung"})
        assert brand.status_code == 200
        assert brand.json()["total"] == 1

        price_filter = await client.get("/api/products/", params={"min_price": 900, "max_price": 1100})
        assert price_filter.status_code == 200
        assert price_filter.json()["total"] == 1

        paginated = await client.get("/api/products/", params={"limit": 1, "offset": 0})
        assert paginated.status_code == 200
        assert len(paginated.json()["products"]) == 1
        assert paginated.json()["total"] == 3


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TEST 3: Full Purchase Flow (e2e)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestFullPurchaseFlow:

    async def test_register_to_delivery(self, client, db_session):
        # 1. Register user
        reg = await _register(client, email="buyer@test.com", username="buyer")
        assert reg.status_code == 201
        user_id = reg.json()["id"]

        h = await _auth(client, "buyer@test.com")

        # 2. Admin creates category + manager creates product
        ah = await _make_admin(client, db_session, "purchadmin@test.com")
        mh = await _make_manager(client, db_session, "purchmgr@test.com")
        cat_id = await _create_category(client, ah, slug="purch-cat")
        prod_id = await _create_product(client, mh, cat_id, name="Headphones", price=150.00, stock=20, sku="PHN-001")

        # 3. User browses catalog
        catalog = await client.get("/api/products/", params={"q": "Headphones"})
        assert catalog.json()["total"] == 1

        # 4. User adds to cart
        add = await _add_cart(client, h, prod_id, qty=3)
        assert add.status_code == 201
        assert add.json()["line_total"] == "450.00"

        # 5. User views cart
        cart = await client.get("/api/cart/", headers=h)
        assert cart.json()["items_count"] == 3
        assert cart.json()["subtotal"] == "450.00"

        # 6. Checkout
        order_resp = await _checkout(client, h,
            delivery_address="456 Oak Ave",
            delivery_method="express",
            notes="Ring doorbell",
        )
        assert order_resp.status_code == 201
        order = order_resp.json()
        assert order["total"] == "450.00"
        assert order["status"] == "pending"
        assert order["delivery_method"] == "express"
        assert order["delivery_address"] == "456 Oak Ave"
        assert len(order["items"]) == 1
        assert order["items"][0]["quantity"] == 3
        assert order["items"][0]["price"] == "150.00"

        # 7. Cart is cleared
        cart_after = await client.get("/api/cart/", headers=h)
        assert cart_after.json()["items_count"] == 0

        # 8. Stock is decremented
        prod_check = await client.get(f"/api/products/{prod_id}")
        assert prod_check.json()["stock"] == 17

        # 9. Payment
        pay = await client.post("/api/payments/", json={
            "order_id": order["id"], "method": "card",
        }, headers=h)
        assert pay.status_code == 201
        assert pay.json()["status"] == "success"
        assert pay.json()["amount"] == "450.00"

        # 10. Order is now paid
        order_check = await client.get(f"/api/orders/{order['id']}", headers=h)
        assert order_check.json()["status"] == "paid"

        # 11. User sees order in history
        history = await client.get("/api/orders/", headers=h)
        assert history.json()["total"] == 1

        # 12. User has notification
        notifs = await client.get("/api/notifications/", headers=h)
        assert notifs.json()["total"] >= 1

    async def test_multi_product_checkout_stock_consistency(self, client, db_session):
        await _register(client, email="multi@test.com", username="multiuser")
        h = await _auth(client, "multi@test.com")

        ah = await _make_admin(client, db_session, "multadmin@test.com")
        mh = await _make_manager(client, db_session, "multmgr@test.com")
        cat_id = await _create_category(client, ah, slug="mult-cat")

        p1 = await _create_product(client, mh, cat_id, name="A", price=10.00, stock=5, sku="MULT-A")
        p2 = await _create_product(client, mh, cat_id, name="B", price=20.00, stock=3, sku="MULT-B")

        await _add_cart(client, h, p1, qty=2)
        await _add_cart(client, h, p2, qty=1)

        order_resp = await _checkout(client, h)
        assert order_resp.status_code == 201
        assert order_resp.json()["total"] == "40.00"

        # Verify DB state
        r1 = await db_session.execute(select(Product).where(Product.id == p1))
        r2 = await db_session.execute(select(Product).where(Product.id == p2))
        assert r1.scalar_one().stock == 3
        assert r2.scalar_one().stock == 2

        order_count = await db_session.execute(select(func.count(Order.id)))
        assert order_count.scalar() == 1


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TEST 4: Admin Panel E2E
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestAdminPanelE2E:

    async def test_admin_user_management(self, client, db_session):
        ah = await _make_admin(client, db_session, "admusr@test.com")
        await _register(client, email="target@test.com", username="target")

        # List users
        users = await client.get("/api/admin/users", headers=ah)
        assert users.status_code == 200
        assert users.json()["total"] >= 2

        # Get target user id
        target_user = None
        for u in users.json()["users"]:
            if u["email"] == "target@test.com":
                target_user = u
                break
        assert target_user is not None

        # Block
        block = await client.patch(f"/api/admin/users/{target_user['id']}/block", headers=ah)
        assert block.status_code == 200
        assert block.json()["is_active"] is False

        # Unblock
        unblock = await client.patch(f"/api/admin/users/{target_user['id']}/unblock", headers=ah)
        assert unblock.status_code == 200
        assert unblock.json()["is_active"] is True

        # Change role
        role = await client.patch(
            f"/api/admin/users/{target_user['id']}/role",
            params={"role": "manager"}, headers=ah,
        )
        assert role.status_code == 200
        assert role.json()["role"] == "manager"

        # Invalid role
        bad_role = await client.patch(
            f"/api/admin/users/{target_user['id']}/role",
            params={"role": "superadmin"}, headers=ah,
        )
        assert bad_role.status_code == 400

    async def test_admin_stats_with_data(self, client, db_session):
        ah = await _make_admin(client, db_session, "sttsadmin@test.com")
        mh = await _make_manager(client, db_session, "sttsmgr@test.com")
        await _register(client, email="sttsbuyer@test.com", username="sttsbuyer")
        bh = await _auth(client, "sttsbuyer@test.com")

        cat_id = await _create_category(client, ah, slug="stts-cat")
        prod_id = await _create_product(client, mh, cat_id, name="SttsWidget", price=75.00, stock=10, sku="STTS-1")

        await _add_cart(client, bh, prod_id, qty=2)
        await _checkout(client, bh)

        stats = await client.get("/api/admin/stats", headers=ah)
        assert stats.status_code == 200
        data = stats.json()
        assert data["total_users"] >= 3
        assert data["total_products"] >= 1
        assert data["total_orders"] >= 1

    async def test_admin_popular_products(self, client, db_session):
        ah = await _make_admin(client, db_session, "popadmin@test.com")
        mh = await _make_manager(client, db_session, "popmgr@test.com")
        await _register(client, email="popbuyer@test.com", username="popbuyer")
        bh = await _auth(client, "popbuyer@test.com")

        cat_id = await _create_category(client, ah, slug="pop-cat")
        p1 = await _create_product(client, mh, cat_id, name="Popular", price=10.00, stock=100, sku="POP-1")
        p2 = await _create_product(client, mh, cat_id, name="Unpopular", price=20.00, stock=100, sku="POP-2")

        await _add_cart(client, bh, p1, qty=5)
        await _checkout(client, bh)
        await _add_cart(client, bh, p2, qty=1)
        await _checkout(client, bh)

        popular = await client.get("/api/admin/popular-products", headers=ah)
        assert popular.status_code == 200
        items = popular.json()
        assert len(items) >= 1
        # Most popular product should be the one with more sales
        assert items[0]["name"] == "Popular"
        assert items[0]["total_sold"] >= 5


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TEST 5: Reviews + Favorites E2E
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestReviewsFavoritesE2E:

    async def test_favorite_and_review_flow(self, client, db_session):
        ah = await _make_admin(client, db_session, "favadmin@test.com")
        mh = await _make_manager(client, db_session, "favmgr@test.com")
        await _register(client, email="favuser@test.com", username="favuser")
        h = await _auth(client, "favuser@test.com")

        cat_id = await _create_category(client, ah, slug="fav-cat")
        prod_id = await _create_product(client, mh, cat_id, name="FavWidget", price=25.00, stock=50, sku="FAV-1")

        # Add to favorites
        fav = await client.post(f"/api/favorites/{prod_id}", headers=h)
        assert fav.status_code == 201

        # List favorites
        favs = await client.get("/api/favorites/", headers=h)
        assert favs.json()["total"] == 1

        # Duplicate favorite
        dup = await client.post(f"/api/favorites/{prod_id}", headers=h)
        assert dup.status_code == 409

        # Create review
        rev = await client.post("/api/reviews/", json={
            "product_id": prod_id, "rating": 5, "text": "Excellent!",
        }, headers=h)
        assert rev.status_code == 201
        assert rev.json()["rating"] == 5

        # Unmoderated review not in public list
        pub_list = await client.get(f"/api/reviews/product/{prod_id}")
        assert pub_list.json()["total"] == 0

        # Admin moderates
        await client.patch(f"/api/reviews/{rev.json()['id']}/moderate", headers=ah)

        # Now visible
        pub_list2 = await client.get(f"/api/reviews/product/{prod_id}")
        assert pub_list2.json()["total"] == 1

        # Duplicate review
        dup_rev = await client.post("/api/reviews/", json={
            "product_id": prod_id, "rating": 4, "text": "Good",
        }, headers=h)
        assert dup_rev.status_code == 409

        # Remove from favorites
        rm = await client.delete(f"/api/favorites/{prod_id}", headers=h)
        assert rm.status_code == 204

        favs_after = await client.get("/api/favorites/", headers=h)
        assert favs_after.json()["total"] == 0

    async def test_cross_user_reviews(self, client, db_session):
        ah = await _make_admin(client, db_session, "xrevadmin@test.com")
        mh = await _make_manager(client, db_session, "xrevmgr@test.com")

        cat_id = await _create_category(client, ah, slug="xrev-cat")
        prod_id = await _create_product(client, mh, cat_id, name="XRev", price=30.00, stock=50, sku="XREV-1")

        await _register(client, email="xrev1@test.com", username="xrev1")
        h1 = await _auth(client, "xrev1@test.com")

        await _register(client, email="xrev2@test.com", username="xrev2")
        h2 = await _auth(client, "xrev2@test.com")

        r1 = await client.post("/api/reviews/", json={
            "product_id": prod_id, "rating": 5, "text": "Great!",
        }, headers=h1)
        r2 = await client.post("/api/reviews/", json={
            "product_id": prod_id, "rating": 3, "text": "OK",
        }, headers=h2)
        assert r1.status_code == 201
        assert r2.status_code == 201

        # Each can see their own, but not public yet
        pub = await client.get(f"/api/reviews/product/{prod_id}")
        assert pub.json()["total"] == 0


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TEST 6: Payment + Webhook E2E
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestPaymentWebhookE2E:

    async def test_full_payment_with_webhook_refund(self, client, db_session):
        ah = await _make_admin(client, db_session, "whadmin@test.com")
        mh = await _make_manager(client, db_session, "whmgr@test.com")
        await _register(client, email="whbuyer@test.com", username="whbuyer")
        h = await _auth(client, "whbuyer@test.com")

        cat_id = await _create_category(client, ah, slug="wh-cat")
        prod_id = await _create_product(client, mh, cat_id, name="WhWidget", price=100.00, stock=10, sku="WH-1")

        await _add_cart(client, h, prod_id, qty=1)
        order_resp = await _checkout(client, h)
        order_id = order_resp.json()["id"]

        # Pay
        pay = await client.post("/api/payments/", json={
            "order_id": order_id, "method": "card",
        }, headers=h)
        assert pay.status_code == 201
        provider_id = pay.json()["provider_payment_id"]
        payment_id = pay.json()["id"]

        # Verify order is paid
        o1 = await client.get(f"/api/orders/{order_id}", headers=h)
        assert o1.json()["status"] == "paid"

        # Webhook: refund
        wh = await client.post("/api/payments/webhook", json={
            "provider_payment_id": provider_id, "status": "refunded",
        })
        assert wh.status_code == 200

        # Payment is refunded
        pay_check = await client.get(f"/api/payments/{payment_id}", headers=h)
        assert pay_check.json()["status"] == "refunded"

        # Admin updates order status after refund
        adm_h = await _make_admin(client, db_session, "whadmin2@test.com")
        status_resp = await client.patch(
            f"/api/orders/{order_id}/status",
            json={"status": "cancelled"}, headers=adm_h,
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "cancelled"

    async def test_payment_access_control(self, client, db_session):
        ah = await _make_admin(client, db_session, "payac@test.com")
        mh = await _make_manager(client, db_session, "payacm@test.com")

        cat_id = await _create_category(client, ah, slug="payac-cat")
        prod_id = await _create_product(client, mh, cat_id, name="PayAC", price=50.00, stock=10, sku="PAYAC-1")

        # User A creates order
        await _register(client, email="usera@test.com", username="usera")
        ha = await _auth(client, "usera@test.com")
        await _add_cart(client, ha, prod_id, qty=1)
        order = (await _checkout(client, ha)).json()

        # User B tries to pay for User A's order
        await _register(client, email="userb@test.com", username="userb")
        hb = await _auth(client, "userb@test.com")
        resp = await client.post("/api/payments/", json={
            "order_id": order["id"], "method": "card",
        }, headers=hb)
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TEST 7: Notifications E2E
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestNotificationsE2E:

    async def test_notifications_through_lifecycle(self, client, db_session):
        ah = await _make_admin(client, db_session, "notifadmin@test.com")
        mh = await _make_manager(client, db_session, "notifmgr@test.com")

        cat_id = await _create_category(client, ah, slug="notif-cat")
        prod_id = await _create_product(client, mh, cat_id, name="NotifWidget", price=50.00, stock=10, sku="NF-1")

        # Register triggers welcome notification
        await _register(client, email="notifuser@test.com", username="notifuser")
        h = await _auth(client, "notifuser@test.com")

        notifs = await client.get("/api/notifications/", headers=h)
        assert notifs.json()["total"] >= 1
        assert notifs.json()["unread_count"] >= 1

        # Checkout triggers order notification
        await _add_cart(client, h, prod_id, qty=1)
        await _checkout(client, h)

        notifs2 = await client.get("/api/notifications/", headers=h)
        assert notifs2.json()["total"] >= 2

        # Mark one as read
        first_id = notifs2.json()["notifications"][0]["id"]
        await client.post(f"/api/notifications/{first_id}/read", headers=h)

        notifs3 = await client.get("/api/notifications/", headers=h)
        assert notifs3.json()["unread_count"] == notifs2.json()["unread_count"] - 1

        # Mark all read
        await client.post("/api/notifications/read-all", headers=h)
        notifs4 = await client.get("/api/notifications/", headers=h)
        assert notifs4.json()["unread_count"] == 0

    async def test_task_status_and_stats(self, client, db_session):
        await _register(client, email="taskuser@test.com", username="taskuser")
        h = await _auth(client, "taskuser@test.com")

        stats = await client.get("/api/notifications/tasks", headers=h)
        assert stats.status_code == 200
        assert "pending" in stats.json()
        assert "completed" in stats.json()

        cleanup = await client.get("/api/notifications/cleanup", headers=h)
        assert cleanup.status_code == 200


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TEST 8: Order Lifecycle
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestOrderLifecycle:

    async def test_order_status_transitions(self, client, db_session):
        ah = await _make_admin(client, db_session, "ordadmin@test.com")
        mh = await _make_manager(client, db_session, "ordmgr@test.com")
        await _register(client, email="orduser@test.com", username="orduser")
        h = await _auth(client, "orduser@test.com")

        cat_id = await _create_category(client, ah, slug="ord-cat")
        prod_id = await _create_product(client, mh, cat_id, name="OrdWidget", price=40.00, stock=20, sku="ORD-1")

        await _add_cart(client, h, prod_id, qty=2)
        order = (await _checkout(client, h)).json()
        assert order["status"] == "pending"

        # Pending → paid (via payment)
        await client.post("/api/payments/", json={
            "order_id": order["id"], "method": "card",
        }, headers=h)
        o = await client.get(f"/api/orders/{order['id']}", headers=h)
        assert o.json()["status"] == "paid"

        # Paid → processing → shipped → completed
        for next_status in ["processing", "shipped", "completed"]:
            resp = await client.patch(
                f"/api/orders/{order['id']}/status",
                json={"status": next_status}, headers=ah,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == next_status

        final = await client.get(f"/api/orders/{order['id']}", headers=h)
        assert final.json()["status"] == "completed"

    async def test_order_list_and_detail(self, client, db_session):
        ah = await _make_admin(client, db_session, "ordlstadmin@test.com")
        mh = await _make_manager(client, db_session, "ordlmgr@test.com")
        await _register(client, email="ordlst@test.com", username="ordlst")
        h = await _auth(client, "ordlst@test.com")

        cat_id = await _create_category(client, ah, slug="ordlst-cat")
        p1 = await _create_product(client, mh, cat_id, name="L1", price=10.00, stock=50, sku="LST-1")
        p2 = await _create_product(client, mh, cat_id, name="L2", price=20.00, stock=50, sku="LST-2")

        await _add_cart(client, h, p1, qty=1)
        await _add_cart(client, h, p2, qty=3)
        order = (await _checkout(client, h)).json()

        assert order["total"] == "70.00"
        assert len(order["items"]) == 2

        detail = await client.get(f"/api/orders/{order['id']}", headers=h)
        assert detail.json()["id"] == order["id"]

        history = await client.get("/api/orders/", headers=h)
        assert history.json()["total"] == 1

        # Admin can see all orders
        admin_list = await client.get("/api/orders/admin/all", headers=ah)
        assert admin_list.json()["total"] >= 1


# ═══════════════════════════════════════════════════════════════
# INTEGRATION TEST 9: Promo Code E2E
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestPromoCodeE2E:

    async def test_promo_crud_and_apply(self, client, db_session):
        ah = await _make_admin(client, db_session, "promoadmin@test.com")

        # Create promo
        create = await client.post("/api/promo-codes/", json={
            "code": "WELCOME10", "discount_type": "percentage",
            "discount_value": 10, "max_uses": 100,
        }, headers=ah)
        assert create.status_code == 201
        promo_id = create.json()["id"]

        # List promos
        listing = await client.get("/api/promo-codes/", headers=ah)
        assert listing.json()["total"] == 1

        # Apply promo
        apply = await client.post("/api/promo-codes/apply", json={"code": "WELCOME10"})
        assert apply.status_code == 200
        assert apply.json()["discount_type"] == "percentage"

        # Delete promo
        delete = await client.delete(f"/api/promo-codes/{promo_id}", headers=ah)
        assert delete.status_code == 204

        # Apply deleted promo
        apply2 = await client.post("/api/promo-codes/apply", json={"code": "WELCOME10"})
        assert apply2.status_code == 404

    async def test_promo_expiration_workflow(self, client, db_session):
        ah = await _make_admin(client, db_session, "promoexpadmin@test.com")

        # Create expired promo
        past = datetime.now(timezone.utc) - timedelta(days=1)
        await client.post("/api/promo-codes/", json={
            "code": "EXPIRED", "discount_type": "fixed",
            "discount_value": 5.00, "expires_at": past.isoformat(),
        }, headers=ah)

        resp = await client.post("/api/promo-codes/apply", json={"code": "EXPIRED"})
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()

        # Create future promo
        future = datetime.now(timezone.utc) + timedelta(days=30)
        await client.post("/api/promo-codes/", json={
            "code": "FUTURE20", "discount_type": "percentage",
            "discount_value": 20, "expires_at": future.isoformat(),
        }, headers=ah)

        resp2 = await client.post("/api/promo-codes/apply", json={"code": "FUTURE20"})
        assert resp2.status_code == 200
