import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User
from app.models.category import Category


async def _setup_category(db_session: AsyncSession):
    cat = Category(name="Electronics", slug="electronics")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat.id


async def _manager_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="mgr-prod-id",
        email="mgrprod@test.com",
        username="mgrprod",
        hashed_password=hash_password("secret123"),
        role="manager",
    ))
    await db_session.commit()
    return create_access_token("mgr-prod-id")


async def _admin_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="adm-prod-id",
        email="admprod@test.com",
        username="admprod",
        hashed_password=hash_password("secret123"),
        role="admin",
    ))
    await db_session.commit()
    return create_access_token("adm-prod-id")


async def _user_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="usr-prod-id",
        email="usrprod@test.com",
        username="usrprod",
        hashed_password=hash_password("secret123"),
        role="user",
    ))
    await db_session.commit()
    return create_access_token("usr-prod-id")


@pytest.mark.asyncio
async def test_list_products_empty(client):
    response = await client.get("/api/products/")
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_create_product(client, db_session):
    token = await _manager_token(db_session)
    cat_id = await _setup_category(db_session)
    response = await client.post(
        "/api/products/",
        json={
            "name": "iPhone 15",
            "slug": "iphone-15",
            "price": "999.99",
            "sku": "IPH-15",
            "stock": 10,
            "category_id": cat_id,
            "brand": "Apple",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "iPhone 15"
    assert data["price"] == "999.99"
    assert data["sku"] == "IPH-15"


@pytest.mark.asyncio
async def test_create_product_user_denied(client, db_session):
    token = await _user_token(db_session)
    cat_id = await _setup_category(db_session)
    response = await client.post(
        "/api/products/",
        json={
            "name": "Test",
            "slug": "test",
            "price": "10.00",
            "sku": "TST-1",
            "category_id": cat_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_product_duplicate_slug(client, db_session):
    token = await _manager_token(db_session)
    cat_id = await _setup_category(db_session)
    await client.post(
        "/api/products/",
        json={
            "name": "Widget",
            "slug": "widget",
            "price": "5.00",
            "sku": "WGT-1",
            "category_id": cat_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.post(
        "/api/products/",
        json={
            "name": "Widget 2",
            "slug": "widget",
            "price": "10.00",
            "sku": "WGT-2",
            "category_id": cat_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_product(client, db_session):
    token = await _manager_token(db_session)
    cat_id = await _setup_category(db_session)
    create_resp = await client.post(
        "/api/products/",
        json={
            "name": "Laptop",
            "slug": "laptop",
            "price": "1499.00",
            "sku": "LPT-1",
            "category_id": cat_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    prod_id = create_resp.json()["id"]

    response = await client.get(f"/api/products/{prod_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Laptop"


@pytest.mark.asyncio
async def test_get_product_not_found(client):
    response = await client.get("/api/products/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_product(client, db_session):
    token = await _manager_token(db_session)
    cat_id = await _setup_category(db_session)
    create_resp = await client.post(
        "/api/products/",
        json={
            "name": "Old Name",
            "slug": "old-name",
            "price": "10.00",
            "sku": "OLD-1",
            "category_id": cat_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    prod_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/products/{prod_id}",
        json={
            "name": "New Name",
            "slug": "new-name",
            "price": "20.00",
            "sku": "NEW-1",
            "category_id": cat_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_product(client, db_session):
    token_adm = await _admin_token(db_session)
    token_mgr = await _manager_token(db_session)
    cat_id = await _setup_category(db_session)
    create_resp = await client.post(
        "/api/products/",
        json={
            "name": "To Delete",
            "slug": "to-delete",
            "price": "5.00",
            "sku": "DEL-1",
            "category_id": cat_id,
        },
        headers={"Authorization": f"Bearer {token_mgr}"},
    )
    prod_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/products/{prod_id}",
        headers={"Authorization": f"Bearer {token_adm}"},
    )
    assert response.status_code == 204

    get_resp = await client.get(f"/api/products/{prod_id}")
    assert get_resp.status_code == 404
