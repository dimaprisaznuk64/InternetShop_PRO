"""End-to-end smoke test against the LIVE production stack (DEBUG=false).

Runs the full user journey:
register -> login -> catalog -> product -> cart -> promo -> checkout ->
payment -> webhook (HMAC-signed) -> order(paid) -> review -> notification.

Usage:
    python scripts/smoke_e2e.py [--base http://localhost:8000]

Env:
    WEBHOOK_SECRET  - must match the backend's WEBHOOK_SECRET (default from .env.docker)
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import uuid

import httpx

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


def section(name: str):
    print(f"\n=== {name} ===")


def expect(resp: httpx.Response, code: int, label: str) -> dict:
    ok = resp.status_code == code
    print(f"{'PASS' if ok else 'FAIL'} {label}: {resp.status_code} (expected {code})")
    if not ok:
        print(f"  body: {resp.text[:300]}")
        sys.exit(1)
    return resp.json() if resp.text else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    client = httpx.Client(base_url=base, timeout=30)
    tag = uuid.uuid4().hex[:8]
    email = f"smoke-{tag}@example.com"
    username = f"smoke_{tag}"
    password = "SmokeTest123!"

    health = client.get("/health")
    assert health.status_code == 200, health.text
    hjson = health.json()
    print(f"/health: {hjson}")
    assert hjson["redis"] == "connected"
    assert hjson["celery"] == "connected"

    # ── auth ─────────────────────────────────────────────────────────
    section("auth")
    user = expect(
        client.post(
            "/api/auth/register",
            json={"email": email, "username": username, "password": password},
        ),
        201,
        "register",
    )
    tokens = expect(
        client.post("/api/auth/login", json={"email": email, "password": password}),
        200,
        "login",
    )
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me = expect(client.get("/api/auth/me", headers=headers), 200, "me")
    assert me["id"] == user["id"]

    # duplicate register must fail with 409
    dup = client.post(
        "/api/auth/register",
        json={"email": email, "username": f"x_{tag}", "password": password},
    )
    expect(dup, 409, "duplicate email rejected")

    # ── catalog / product ────────────────────────────────────────────
    section("catalog & product")
    products = expect(client.get("/api/products/", params={"page_size": 50}), 200, "catalog list")
    items = products["products"]
    in_stock = [p for p in items if p.get("stock", 0) > 0]
    assert in_stock, "catalog has no products in stock"
    product_id = in_stock[0]["id"]
    detail = expect(client.get(f"/api/products/{product_id}"), 200, "product detail")

    search = expect(client.get("/api/products/", params={"search": detail["name"][:4]}), 200, "search")
    assert any(p["id"] == product_id for p in search["products"]), "ILIKE search lost the product"

    # ── promo (admin-only creation; ADMIN_* env of a pre-elevated local admin) ──
    section("promo")
    assert ADMIN_EMAIL and ADMIN_PASSWORD, (
        "Set ADMIN_EMAIL / ADMIN_PASSWORD of a local admin to test promo creation"
    )
    admin_tokens = expect(
        client.post(
            "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        ),
        200,
        "admin login",
    )
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    promo_code = f"SMOKE{tag}".upper()
    expect(
        client.post(
            "/api/promo-codes/",
            json={
                "code": promo_code,
                "discount_type": "percentage",
                "discount_value": 10,
                "expires_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 3600)),
            },
            headers=admin_headers,
        ),
        201,
        "promo create (admin)",
    )

    apply = expect(client.post("/api/promo-codes/apply", json={"code": promo_code}), 200, "promo apply preview")
    print(f"  discount computed: {apply}")

    # ── cart ─────────────────────────────────────────────────────────
    section("cart")
    cart = expect(
        client.post(
            "/api/cart/items",
            json={"product_id": product_id, "quantity": 1},
            headers=headers,
        ),
        201,
        "add to cart",
    )
    cart_items = cart["items"]
    assert cart_items, "cart response has no items"
    assert "product_image" in cart_items[0], "cart contract missing product_image"

    # ── checkout ─────────────────────────────────────────────────────
    section("checkout")
    order = expect(
        client.post(
            "/api/orders/checkout",
            json={
                "delivery_method": "courier",
                "delivery_address": "Smoke St. 1",
                "promo_code": promo_code,
            },
            headers=headers,
        ),
        201,
        "checkout",
    )
    order_id = order["id"]
    total = float(order["total"])
    print(f"  order {order_id}: total={total}, status={order['status']}")
    assert total > 0

    # ── payment + webhook ────────────────────────────────────────────
    section("payment & webhook")
    payment = expect(
        client.post(
            "/api/payments/",
            json={"order_id": order_id, "method": "card"},
            headers=headers,
        ),
        201,
        "create payment",
    )
    provider_payment_id = payment["provider_payment_id"]

    unsigned = client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": provider_payment_id, "status": "success"},
    )
    if WEBHOOK_SECRET:
        expect(unsigned, 400, "unsigned webhook rejected (fail-closed)")

    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        f"{provider_payment_id}:success".encode(),
        hashlib.sha256,
    ).hexdigest()
    expect(
        client.post(
            "/api/payments/webhook",
            json={"provider_payment_id": provider_payment_id, "status": "success"},
            headers={"X-Webhook-Signature": signature},
        ),
        200,
        "signed webhook accepted",
    )

    paid = expect(client.get(f"/api/orders/{order_id}", headers=headers), 200, "order after webhook")
    assert paid["status"] == "paid", f"expected paid, got {paid['status']}"

    bad_sig = client.post(
        "/api/payments/webhook",
        json={"provider_payment_id": provider_payment_id, "status": "refunded"},
        headers={"X-Webhook-Signature": "deadbeef"},
    )
    expect(bad_sig, 400, "bad signature rejected")

    # ── review ───────────────────────────────────────────────────────
    section("review")
    review = expect(
        client.post(
            "/api/reviews/",
            json={"product_id": product_id, "rating": 5, "text": "Smoke test purchase — great!"},
            headers=headers,
        ),
        201,
        "create review",
    )
    reviews = expect(client.get(f"/api/reviews/product/{product_id}"), 200, "list reviews")
    listed_ids = [r["id"] for r in reviews["reviews"]]
    if review["id"] in listed_ids:
        print("  review visible immediately")
    else:
        # reviews are moderated before appearing in the public list
        assert review["is_moderated"] is False, "review hidden but not marked unmoderated"
        print("  review created and awaiting moderation (by design)")

    # ── notifications ────────────────────────────────────────────────
    section("notifications")
    notif = expect(client.get("/api/notifications/", headers=headers), 200, "list notifications")
    n_items = notif["notifications"]
    assert len(n_items) >= 2, f"expected >=2 notifications (welcome+order), got {len(n_items)}"
    for n in n_items:
        print(f"  - [{n['type']}] {n['title']}")

    # logout blacklists the refresh token (in-process blacklist, single instance)
    section("logout")
    expect(
        client.post(
            "/api/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers=headers,
        ),
        204,
        "logout",
    )
    reuse = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    print(f"refresh-token reuse after logout: {reuse.status_code} (401 = blacklist works)")

    print("\n" + "=" * 50)
    print("E2E SMOKE: ALL STEPS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()
