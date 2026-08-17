import pytest
from app.utils.security import create_access_token, hash_password
from app.database import AsyncSession
from sqlalchemy import insert
from app.models.user import User
from app.models.category import Category
from app.models.product import Product


async def _setup_data(db_session: AsyncSession):
    cat = Category(name="Phones3", slug="phones3")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    products = [
        Product(name="iPhone 15", slug="ip15", price=999.00, sku="S-IPH-15", stock=10, category_id=cat.id, brand="Apple"),
        Product(name="Samsung Galaxy", slug="sg", price=799.00, sku="S-SAM-G", stock=5, category_id=cat.id, brand="Samsung"),
        Product(name="Pixel 8", slug="px8", price=699.00, sku="S-PXL-8", stock=0, category_id=cat.id, brand="Google"),
    ]
    for p in products:
        db_session.add(p)
    await db_session.commit()
    return cat.id


async def _user_token(db_session: AsyncSession):
    await db_session.execute(insert(User).values(
        id="srch-user-id",
        email="srch@test.com",
        username="srchuser",
        hashed_password=hash_password("secret123"),
        role="user",
    ))
    await db_session.commit()
    return create_access_token("srch-user-id")


@pytest.mark.asyncio
async def test_search_by_name(client, db_session):
    token = await _user_token(db_session)
    await _setup_data(db_session)

    response = await client.get(
        "/api/products/?q=iPhone",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["products"][0]["name"] == "iPhone 15"


@pytest.mark.asyncio
async def test_search_by_sku(client, db_session):
    token = await _user_token(db_session)
    await _setup_data(db_session)

    response = await client.get(
        "/api/products/?q=SAM",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_filter_by_category(client, db_session):
    token = await _user_token(db_session)
    cat_id = await _setup_data(db_session)

    response = await client.get(
        f"/api/products/?category_id={cat_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 3


@pytest.mark.asyncio
async def test_filter_by_price_range(client, db_session):
    token = await _user_token(db_session)
    await _setup_data(db_session)

    response = await client.get(
        "/api/products/?min_price=700&max_price=850",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["products"][0]["name"] == "Samsung Galaxy"


@pytest.mark.asyncio
async def test_filter_in_stock(client, db_session):
    token = await _user_token(db_session)
    await _setup_data(db_session)

    response = await client.get(
        "/api/products/?in_stock=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2


@pytest.mark.asyncio
async def test_filter_by_brand(client, db_session):
    token = await _user_token(db_session)
    await _setup_data(db_session)

    response = await client.get(
        "/api/products/?brand=google",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_sort_by_price_asc(client, db_session):
    token = await _user_token(db_session)
    await _setup_data(db_session)

    response = await client.get(
        "/api/products/?sort_by=price&sort_order=asc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    names = [p["name"] for p in response.json()["products"]]
    assert names == ["Pixel 8", "Samsung Galaxy", "iPhone 15"]


@pytest.mark.asyncio
async def test_pagination(client, db_session):
    token = await _user_token(db_session)
    await _setup_data(db_session)

    response = await client.get(
        "/api/products/?limit=2&offset=0&sort_by=price&sort_order=asc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["products"]) == 2
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_search_no_results(client, db_session):
    token = await _user_token(db_session)
    await _setup_data(db_session)

    response = await client.get(
        "/api/products/?q=nonexistent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0
