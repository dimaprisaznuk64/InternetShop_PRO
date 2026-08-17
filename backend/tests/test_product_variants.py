import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User
from app.models.category import Category
from app.models.product import Product


async def _setup_product(db_session: AsyncSession):
    cat = Category(name="Phones2", slug="phones2")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    product = Product(
        name="iPhone 15",
        slug="iphone-15-var",
        price=999.00,
        sku="IPH-15-V",
        category_id=cat.id,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product.id


async def _manager_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="mgr-var-id",
        email="mgrvar@test.com",
        username="mgrvar",
        hashed_password=hash_password("secret123"),
        role="manager",
    ))
    await db_session.commit()
    return create_access_token("mgr-var-id")


@pytest.mark.asyncio
async def test_list_variants_empty(client, db_session):
    prod_id = await _setup_product(db_session)
    response = await client.get(f"/api/products/{prod_id}/variants/")
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_create_variant(client, db_session):
    token = await _manager_token(db_session)
    prod_id = await _setup_product(db_session)
    response = await client.post(
        f"/api/products/{prod_id}/variants/",
        json={
            "name": "Black 128GB",
            "sku": "IPH-15-B128",
            "price": "999.00",
            "stock": 5,
            "attributes": "color:black,storage:128GB",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Black 128GB"
    assert data["sku"] == "IPH-15-B128"


@pytest.mark.asyncio
async def test_get_variant(client, db_session):
    token = await _manager_token(db_session)
    prod_id = await _setup_product(db_session)
    create_resp = await client.post(
        f"/api/products/{prod_id}/variants/",
        json={"name": "White", "sku": "IPH-15-W", "price": "999.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    var_id = create_resp.json()["id"]

    response = await client.get(f"/api/products/{prod_id}/variants/{var_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "White"


@pytest.mark.asyncio
async def test_get_variant_not_found(client, db_session):
    prod_id = await _setup_product(db_session)
    response = await client.get(f"/api/products/{prod_id}/variants/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_variant(client, db_session):
    token = await _manager_token(db_session)
    prod_id = await _setup_product(db_session)
    create_resp = await client.post(
        f"/api/products/{prod_id}/variants/",
        json={"name": "Old", "sku": "OLD-V", "price": "10.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    var_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/products/{prod_id}/variants/{var_id}",
        json={"name": "New", "sku": "NEW-V", "price": "20.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"


@pytest.mark.asyncio
async def test_delete_variant(client, db_session):
    token = await _manager_token(db_session)
    prod_id = await _setup_product(db_session)
    create_resp = await client.post(
        f"/api/products/{prod_id}/variants/",
        json={"name": "Del", "sku": "DEL-V", "price": "5.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    var_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/products/{prod_id}/variants/{var_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_variant_duplicate_sku(client, db_session):
    token = await _manager_token(db_session)
    prod_id = await _setup_product(db_session)
    await client.post(
        f"/api/products/{prod_id}/variants/",
        json={"name": "V1", "sku": "DUP-V", "price": "10.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.post(
        f"/api/products/{prod_id}/variants/",
        json={"name": "V2", "sku": "DUP-V", "price": "20.00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
