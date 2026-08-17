import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User
from app.models.category import Category
from app.models.product import Product


async def _setup_product(db_session: AsyncSession, stock=10):
    cat = Category(name="CartCat", slug="cart-cat")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    product = Product(
        name="Widget",
        slug="widget-cart",
        price=25.00,
        sku="CART-W-1",
        stock=stock,
        category_id=cat.id,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product.id


async def _auth_header(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="cart-user-id",
        email="cart@test.com",
        username="cartuser",
        hashed_password=hash_password("secret123"),
        role="user",
    ))
    await db_session.commit()
    token = create_access_token("cart-user-id")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_empty_cart(client, db_session):
    headers = await _auth_header(db_session)
    response = await client.get("/api/cart/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items_count"] == 0
    assert data["subtotal"] == "0.00"


@pytest.mark.asyncio
async def test_add_to_cart(client, db_session):
    headers = await _auth_header(db_session)
    prod_id = await _setup_product(db_session)

    response = await client.post(
        "/api/cart/items",
        json={"product_id": prod_id, "quantity": 2},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 2
    assert data["line_total"] == "50.00"

    cart_resp = await client.get("/api/cart/", headers=headers)
    assert cart_resp.json()["items_count"] == 2
    assert cart_resp.json()["subtotal"] == "50.00"


@pytest.mark.asyncio
async def test_add_to_cart_increments(client, db_session):
    headers = await _auth_header(db_session)
    prod_id = await _setup_product(db_session)

    await client.post("/api/cart/items", json={"product_id": prod_id, "quantity": 1}, headers=headers)
    response = await client.post("/api/cart/items", json={"product_id": prod_id, "quantity": 3}, headers=headers)
    assert response.status_code == 201
    assert response.json()["quantity"] == 4


@pytest.mark.asyncio
async def test_add_to_cart_exceeds_stock(client, db_session):
    headers = await _auth_header(db_session)
    prod_id = await _setup_product(db_session, stock=5)

    response = await client.post(
        "/api/cart/items",
        json={"product_id": prod_id, "quantity": 10},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_cart_item(client, db_session):
    headers = await _auth_header(db_session)
    prod_id = await _setup_product(db_session)

    add_resp = await client.post(
        "/api/cart/items",
        json={"product_id": prod_id, "quantity": 1},
        headers=headers,
    )
    item_id = add_resp.json()["id"]

    response = await client.put(
        f"/api/cart/items/{item_id}",
        json={"quantity": 5},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["quantity"] == 5
    assert response.json()["line_total"] == "125.00"


@pytest.mark.asyncio
async def test_remove_cart_item(client, db_session):
    headers = await _auth_header(db_session)
    prod_id = await _setup_product(db_session)

    add_resp = await client.post(
        "/api/cart/items",
        json={"product_id": prod_id, "quantity": 2},
        headers=headers,
    )
    item_id = add_resp.json()["id"]

    response = await client.delete(f"/api/cart/items/{item_id}", headers=headers)
    assert response.status_code == 204

    cart_resp = await client.get("/api/cart/", headers=headers)
    assert cart_resp.json()["items_count"] == 0


@pytest.mark.asyncio
async def test_clear_cart(client, db_session):
    headers = await _auth_header(db_session)
    prod_id = await _setup_product(db_session)

    await client.post("/api/cart/items", json={"product_id": prod_id, "quantity": 3}, headers=headers)

    response = await client.delete("/api/cart/", headers=headers)
    assert response.status_code == 204

    cart_resp = await client.get("/api/cart/", headers=headers)
    assert cart_resp.json()["items_count"] == 0


@pytest.mark.asyncio
async def test_cart_not_found_product(client, db_session):
    headers = await _auth_header(db_session)
    response = await client.post(
        "/api/cart/items",
        json={"product_id": "nonexistent", "quantity": 1},
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cart_no_auth(client):
    response = await client.get("/api/cart/")
    assert response.status_code == 401
