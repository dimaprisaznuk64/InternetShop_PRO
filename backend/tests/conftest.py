import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.utils.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    import app.models  # noqa
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    import os
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
async def db_session():
    async with TestSession() as session:
        yield session
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="fixture@test.com",
        username="fixtureuser",
        hashed_password=hash_password("testpass123"),
        role=UserRole.user,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    user = User(
        email="admin@fixture.com",
        username="fixtureadmin",
        hashed_password=hash_password("testpass123"),
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_manager(db_session: AsyncSession) -> User:
    user = User(
        email="manager@fixture.com",
        username="fixturemanager",
        hashed_password=hash_password("testpass123"),
        role=UserRole.manager,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    return create_access_token(test_user.id)


@pytest.fixture
def admin_token(test_admin: User) -> str:
    return create_access_token(test_admin.id)


@pytest.fixture
def manager_token(test_manager: User) -> str:
    return create_access_token(test_manager.id)


@pytest.fixture
def user_headers(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def manager_headers(manager_token: str) -> dict:
    return {"Authorization": f"Bearer {manager_token}"}


def load_compose_yaml(source) -> dict:
    """Load a Docker Compose file from a path or open file object,
    tolerating compose-specific YAML tags like !override and !reset
    (valid for docker compose, unknown to PyYAML)."""
    import yaml

    class ComposeLoader(yaml.SafeLoader):
        pass

    def _compose_tag(loader, tag_suffix, node):
        if isinstance(node, yaml.ScalarNode):
            return loader.construct_scalar(node)
        if isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node)
        if isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node)
        return None

    ComposeLoader.add_multi_constructor("!", _compose_tag)
    if hasattr(source, "read"):
        return yaml.load(source.read(), Loader=ComposeLoader)
    with open(source, encoding="utf-8") as f:
        return yaml.load(f, Loader=ComposeLoader)
