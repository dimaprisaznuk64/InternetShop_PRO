"""
Docker Compose configuration tests — lesson 62.
Validates docker-compose.yml structure, services, volumes, networking.
"""
import os
import re
import pytest
import yaml


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COMPOSE_PATH = os.path.join(PROJECT_ROOT, "docker-compose.yml")
DOCKERFILE_BACKEND = os.path.join(PROJECT_ROOT, "backend", "Dockerfile")
DOCKERFILE_FRONTEND = os.path.join(PROJECT_ROOT, "frontend", "Dockerfile")
ENTRYPOINT = os.path.join(PROJECT_ROOT, "backend", "entrypoint.sh")
ENV_DOCKER = os.path.join(PROJECT_ROOT, ".env.docker")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def compose() -> dict:
    with open(COMPOSE_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def compose_raw() -> str:
    return read_file(COMPOSE_PATH)


# ─── docker-compose.yml existence ──────────────────────────────────


class TestComposeFileExists:

    def test_compose_file_exists(self):
        assert os.path.isfile(COMPOSE_PATH)

    def test_env_docker_exists(self):
        assert os.path.isfile(ENV_DOCKER)

    def test_entrypoint_exists(self):
        assert os.path.isfile(ENTRYPOINT)


# ─── Services defined ──────────────────────────────────────────────


class TestComposeServices:

    def test_has_services_key(self, compose):
        assert "services" in compose

    def test_has_postgres(self, compose):
        assert "postgres" in compose["services"]

    def test_has_redis(self, compose):
        assert "redis" in compose["services"]

    def test_has_backend(self, compose):
        assert "backend" in compose["services"]

    def test_has_frontend(self, compose):
        assert "frontend" in compose["services"]

    def test_four_services_total(self, compose):
        services = compose["services"]
        assert len(services) >= 4
        for svc in ("postgres", "redis", "backend", "frontend"):
            assert svc in services


# ─── PostgreSQL service ────────────────────────────────────────────


class TestPostgresService:

    def test_uses_postgres_image(self, compose):
        img = compose["services"]["postgres"]["image"]
        assert "postgres" in img

    def test_has_healthcheck(self, compose):
        hc = compose["services"]["postgres"].get("healthcheck")
        assert hc is not None

    def test_has_volume(self, compose):
        volumes = compose["services"]["postgres"].get("volumes", [])
        assert any("pgdata" in v for v in volumes)

    def test_uses_alpine(self, compose):
        img = compose["services"]["postgres"]["image"]
        assert "alpine" in img

    def test_env_vars_for_db(self, compose):
        env = compose["services"]["postgres"].get("environment", {})
        keys = " ".join(env.keys()) if isinstance(env, dict) else str(env)
        assert "POSTGRES" in keys.upper() or "postgres" in keys.lower()


# ─── Redis service ─────────────────────────────────────────────────


class TestRedisService:

    def test_uses_redis_image(self, compose):
        img = compose["services"]["redis"]["image"]
        assert "redis" in img

    def test_has_healthcheck(self, compose):
        hc = compose["services"]["redis"].get("healthcheck")
        assert hc is not None

    def test_has_volume(self, compose):
        volumes = compose["services"]["redis"].get("volumes", [])
        assert any("redisdata" in v for v in volumes)

    def test_uses_alpine(self, compose):
        img = compose["services"]["redis"]["image"]
        assert "alpine" in img


# ─── Backend service ───────────────────────────────────────────────


class TestBackendService:

    def test_builds_from_backend_dir(self, compose):
        build = compose["services"]["backend"].get("build", {})
        if isinstance(build, dict):
            assert "backend" in build.get("context", "")
        else:
            assert "backend" in build

    def test_depends_on_postgres(self, compose):
        deps = compose["services"]["backend"].get("depends_on", {})
        assert "postgres" in deps

    def test_depends_on_redis(self, compose):
        deps = compose["services"]["backend"].get("depends_on", {})
        assert "redis" in deps

    def test_uses_env_file(self, compose):
        env_file = compose["services"]["backend"].get("env_file", [])
        if isinstance(env_file, str):
            env_file = [env_file]
        assert any(".env" in f for f in env_file)

    def test_has_healthcheck(self, compose):
        hc = compose["services"]["backend"].get("healthcheck")
        assert hc is not None

    def test_has_upload_volume(self, compose):
        volumes = compose["services"]["backend"].get("volumes", [])
        assert any("uploads" in v for v in volumes)

    def test_postgres_condition_healthy(self, compose):
        deps = compose["services"]["backend"].get("depends_on", {})
        pg_dep = deps.get("postgres", {})
        if isinstance(pg_dep, dict):
            assert pg_dep.get("condition") == "service_healthy"


# ─── Frontend service ──────────────────────────────────────────────


class TestFrontendService:

    def test_builds_from_frontend_dir(self, compose):
        build = compose["services"]["frontend"].get("build", {})
        if isinstance(build, dict):
            assert "frontend" in build.get("context", "")
        else:
            assert "frontend" in build

    def test_depends_on_backend(self, compose):
        deps = compose["services"]["frontend"].get("depends_on", {})
        assert "backend" in deps

    def test_exposes_port(self, compose):
        ports = compose["services"]["frontend"].get("ports", [])
        assert len(ports) > 0

    def test_backend_condition_healthy(self, compose):
        deps = compose["services"]["frontend"].get("depends_on", {})
        be_dep = deps.get("backend", {})
        if isinstance(be_dep, dict):
            assert be_dep.get("condition") == "service_healthy"


# ─── Volumes ───────────────────────────────────────────────────────


class TestVolumes:

    def test_has_volumes_key(self, compose):
        assert "volumes" in compose

    def test_pgdata_volume(self, compose):
        vols = compose["volumes"]
        assert "pgdata" in vols

    def test_redisdata_volume(self, compose):
        vols = compose["volumes"]
        assert "redisdata" in vols

    def test_uploads_volume(self, compose):
        vols = compose["volumes"]
        assert "uploads" in vols


# ─── Restart policy ────────────────────────────────────────────────


class TestRestartPolicy:

    def test_all_services_have_restart(self, compose):
        for name, svc in compose["services"].items():
            assert "restart" in svc, f"Service '{name}' missing restart policy"

    def test_restart_unless_stopped(self, compose):
        for name, svc in compose["services"].items():
            assert svc["restart"] in ("unless-stopped", "always", "on-failure"), (
                f"Service '{name}' has unexpected restart: {svc['restart']}"
            )


# ─── Entrypoint script ────────────────────────────────────────────


class TestEntrypoint:

    def test_waits_for_postgres(self):
        content = read_file(ENTRYPOINT)
        assert "postgres" in content.lower()

    def test_runs_migrations(self):
        content = read_file(ENTRYPOINT)
        assert "alembic" in content and "upgrade" in content

    def test_starts_uvicorn(self):
        content = read_file(ENTRYPOINT)
        assert "uvicorn" in content

    def test_set_e(self):
        content = read_file(ENTRYPOINT)
        assert "set -e" in content

    def test_exec_replaces_shell(self):
        content = read_file(ENTRYPOINT)
        assert "exec" in content


# ─── Backend Dockerfile entrypoint ─────────────────────────────────


class TestBackendDockerfileEntrypoint:

    def test_entrypoint_in_dockerfile(self):
        content = read_file(DOCKERFILE_BACKEND)
        assert "entrypoint.sh" in content

    def test_uses_entrypoint_directive(self):
        content = read_file(DOCKERFILE_BACKEND)
        assert "ENTRYPOINT" in content


# ─── .env.docker ───────────────────────────────────────────────────


class TestEnvDocker:

    def test_has_database_url(self):
        content = read_file(ENV_DOCKER)
        assert "DATABASE_URL" in content

    def test_database_url_points_to_postgres_service(self):
        content = read_file(ENV_DOCKER)
        assert "postgres:" in content, "DATABASE_URL must use 'postgres' hostname"

    def test_has_secret_key(self):
        content = read_file(ENV_DOCKER)
        assert "SECRET_KEY" in content

    def test_has_redis_url(self):
        content = read_file(ENV_DOCKER)
        assert "REDIS_URL" in content

    def test_redis_url_points_to_redis_service(self):
        content = read_file(ENV_DOCKER)
        assert "redis:" in content, "REDIS_URL must use 'redis' hostname"

    def test_has_cors_origins(self):
        content = read_file(ENV_DOCKER)
        assert "CORS_ORIGINS" in content


# ─── Compose raw content checks ───────────────────────────────────


class TestComposeRaw:

    def test_no_tabs(self, compose_raw):
        for i, line in enumerate(compose_raw.splitlines(), 1):
            assert "\t" not in line, f"Line {i} contains tabs"

    def test_has_version_or_services(self, compose_raw):
        assert "services:" in compose_raw
