import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User
from app.models.category import Category
from app.models.product import Product


async def _setup_product(db_session: AsyncSession):
    cat = Category(name="Phones", slug="phones")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    product = Product(
        name="iPhone",
        slug="iphone",
        price=999.00,
        sku="IPH-001",
        category_id=cat.id,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product.id


async def _manager_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="mgr-img-id",
        email="mgrimg@test.com",
        username="mgrimg",
        hashed_password=hash_password("secret123"),
        role="manager",
    ))
    await db_session.commit()
    return create_access_token("mgr-img-id")


@pytest.mark.asyncio
async def test_list_images_empty(client, db_session):
    prod_id = await _setup_product(db_session)
    response = await client.get(f"/api/products/{prod_id}/images/")
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_add_image(client, db_session):
    token = await _manager_token(db_session)
    prod_id = await _setup_product(db_session)
    response = await client.post(
        f"/api/products/{prod_id}/images/",
        json={"url": "https://example.com/img.jpg", "is_primary": True, "position": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com/img.jpg"
    assert data["is_primary"] is True


@pytest.mark.asyncio
async def test_delete_image(client, db_session):
    token = await _manager_token(db_session)
    prod_id = await _setup_product(db_session)
    create_resp = await client.post(
        f"/api/products/{prod_id}/images/",
        json={"url": "https://example.com/del.jpg"},
        headers={"Authorization": f"Bearer {token}"},
    )
    img_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/products/{prod_id}/images/{img_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    list_resp = await client.get(f"/api/products/{prod_id}/images/")
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_image_not_found(client, db_session):
    token = await _manager_token(db_session)
    prod_id = await _setup_product(db_session)
    response = await client.delete(
        f"/api/products/{prod_id}/images/nonexistent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
