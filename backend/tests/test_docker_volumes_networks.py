"""
Docker Volumes & Networks tests — lesson 63.
Validates named networks, volume drivers, service isolation, persistence.
"""
import os
import pytest
import yaml

from tests.conftest import load_compose_yaml


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COMPOSE_PATH = os.path.join(PROJECT_ROOT, "docker-compose.yml")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def compose() -> dict:
    with open(COMPOSE_PATH, encoding="utf-8") as f:
        return load_compose_yaml(f)


@pytest.fixture(scope="module")
def compose_raw() -> str:
    return read_file(COMPOSE_PATH)


# ─── Networks defined ──────────────────────────────────────────────


class TestNetworksExist:

    def test_has_networks_key(self, compose):
        assert "networks" in compose

    def test_has_backend_net(self, compose):
        assert "backend-net" in compose["networks"]

    def test_has_frontend_net(self, compose):
        assert "frontend-net" in compose["networks"]

    def test_two_networks_total(self, compose):
        assert len(compose["networks"]) == 2


class TestNetworkDrivers:

    def test_backend_net_uses_bridge(self, compose):
        driver = compose["networks"]["backend-net"].get("driver")
        assert driver == "bridge"

    def test_frontend_net_uses_bridge(self, compose):
        driver = compose["networks"]["frontend-net"].get("driver")
        assert driver == "bridge"


# ─── Service network assignments ───────────────────────────────────


class TestServiceNetworks:

    def test_postgres_on_backend_net(self, compose):
        nets = compose["services"]["postgres"].get("networks", [])
        assert "backend-net" in nets

    def test_redis_on_backend_net(self, compose):
        nets = compose["services"]["redis"].get("networks", [])
        assert "backend-net" in nets

    def test_backend_on_both_networks(self, compose):
        nets = compose["services"]["backend"].get("networks", [])
        assert "backend-net" in nets
        assert "frontend-net" in nets

    def test_frontend_on_frontend_net_only(self, compose):
        nets = compose["services"]["frontend"].get("networks", [])
        assert "frontend-net" in nets
        assert "backend-net" not in nets

    def test_all_services_have_networks(self, compose):
        for name, svc in compose["services"].items():
            assert "networks" in svc, f"Service '{name}' missing networks"


# ─── Network isolation ─────────────────────────────────────────────


class TestNetworkIsolation:

    def test_frontend_cannot_reach_postgres_directly(self, compose):
        fe_nets = compose["services"]["frontend"].get("networks", [])
        pg_nets = compose["services"]["postgres"].get("networks", [])
        shared = set(fe_nets) & set(pg_nets)
        assert len(shared) == 0, "Frontend and PostgreSQL must NOT share a network"

    def test_frontend_cannot_reach_redis_directly(self, compose):
        fe_nets = compose["services"]["frontend"].get("networks", [])
        redis_nets = compose["services"]["redis"].get("networks", [])
        shared = set(fe_nets) & set(redis_nets)
        assert len(shared) == 0, "Frontend and Redis must NOT share a network"

    def test_backend_bridge_between_frontend_and_db(self, compose):
        be_nets = set(compose["services"]["backend"].get("networks", []))
        pg_nets = set(compose["services"]["postgres"].get("networks", []))
        fe_nets = set(compose["services"]["frontend"].get("networks", []))
        assert be_nets & pg_nets, "Backend must share network with PostgreSQL"
        assert be_nets & fe_nets, "Backend must share network with Frontend"


# ─── Volumes defined ───────────────────────────────────────────────


class TestVolumesExist:

    def test_has_volumes_key(self, compose):
        assert "volumes" in compose

    def test_has_pgdata(self, compose):
        assert "pgdata" in compose["volumes"]

    def test_has_redisdata(self, compose):
        assert "redisdata" in compose["volumes"]

    def test_has_uploads(self, compose):
        assert "uploads" in compose["volumes"]

    def test_three_volumes_total(self, compose):
        assert len(compose["volumes"]) == 3


class TestVolumeDrivers:

    def test_pgdata_uses_local_driver(self, compose):
        driver = compose["volumes"]["pgdata"].get("driver")
        assert driver == "local"

    def test_redisdata_uses_local_driver(self, compose):
        driver = compose["volumes"]["redisdata"].get("driver")
        assert driver == "local"

    def test_uploads_uses_local_driver(self, compose):
        driver = compose["volumes"]["uploads"].get("driver")
        assert driver == "local"


# ─── Volume mounts per service ─────────────────────────────────────


class TestServiceVolumes:

    def test_postgres_mounts_pgdata(self, compose):
        vols = compose["services"]["postgres"].get("volumes", [])
        assert any("pgdata:/var/lib/postgresql/data" in v for v in vols)

    def test_redis_mounts_redisdata(self, compose):
        vols = compose["services"]["redis"].get("volumes", [])
        assert any("redisdata:/data" in v for v in vols)

    def test_backend_mounts_uploads(self, compose):
        vols = compose["services"]["backend"].get("volumes", [])
        assert any("uploads:/app/uploads" in v for v in vols)

    def test_frontend_no_volumes(self, compose):
        vols = compose["services"]["frontend"].get("volumes", [])
        assert len(vols) == 0, "Frontend should not mount any volumes"


# ─── Persistence guarantees ────────────────────────────────────────


class TestPersistenceGuarantees:

    def test_postgres_data_persisted(self, compose):
        vols = compose["services"]["postgres"].get("volumes", [])
        assert any("pgdata" in v for v in vols)

    def test_redis_data_persisted(self, compose):
        vols = compose["services"]["redis"].get("volumes", [])
        assert any("redisdata" in v for v in vols)

    def test_uploads_persisted(self, compose):
        vols = compose["services"]["backend"].get("volumes", [])
        assert any("uploads" in v for v in vols)


# ─── Port mapping ──────────────────────────────────────────────────


class TestPortMapping:

    def test_postgres_exposed_port(self, compose):
        ports = compose["services"]["postgres"].get("ports", [])
        assert any("5432" in str(p) for p in ports)

    def test_redis_exposed_port(self, compose):
        ports = compose["services"]["redis"].get("ports", [])
        assert any("6379" in str(p) for p in ports)

    def test_backend_exposed_port(self, compose):
        ports = compose["services"]["backend"].get("ports", [])
        assert any("8000" in str(p) for p in ports)

    def test_frontend_exposed_port(self, compose):
        ports = compose["services"]["frontend"].get("ports", [])
        assert any("3000" in str(p) or "80" in str(p) for p in ports)


# ─── Compose raw content ──────────────────────────────────────────


class TestComposeRaw:

    def test_no_tabs(self, compose_raw):
        for i, line in enumerate(compose_raw.splitlines(), 1):
            assert "\t" not in line, f"Line {i} contains tabs"

    def test_networks_section_after_services(self, compose_raw):
        services_pos = compose_raw.find("services:")
        networks_pos = compose_raw.find("networks:")
        assert networks_pos > services_pos

    def test_volumes_section_after_networks(self, compose_raw):
        networks_pos = compose_raw.find("networks:")
        volumes_pos = compose_raw.rfind("volumes:")
        assert volumes_pos > networks_pos
