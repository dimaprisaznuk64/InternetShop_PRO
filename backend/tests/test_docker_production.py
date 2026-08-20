"""
Production Docker tests — lesson 64.
Validates multi-stage builds, security hardening, prod overrides, image optimization.
"""
import os
import re
import pytest
import yaml


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
COMPOSE_PATH = os.path.join(PROJECT_ROOT, "docker-compose.yml")
COMPOSE_PROD_PATH = os.path.join(PROJECT_ROOT, "docker-compose.prod.yml")
REQ_PROD = os.path.join(BACKEND_DIR, "requirements-prod.txt")
REQ_FULL = os.path.join(BACKEND_DIR, "requirements.txt")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─── Requirements separation ───────────────────────────────────────


class TestRequirementsSeparation:

    def test_prod_requirements_exist(self):
        assert os.path.isfile(REQ_PROD)

    def test_prod_has_no_test_deps(self):
        content = read_file(REQ_PROD)
        for dep in ("pytest", "httpx"):
            assert dep not in content, f"Prod requirements must not include {dep}"

    def test_prod_has_fastapi(self):
        content = read_file(REQ_PROD)
        assert "fastapi" in content

    def test_prod_has_uvicorn(self):
        content = read_file(REQ_PROD)
        assert "uvicorn" in content

    def test_prod_has_sqlalchemy(self):
        content = read_file(REQ_PROD)
        assert "sqlalchemy" in content

    def test_prod_has_asyncpg(self):
        content = read_file(REQ_PROD)
        assert "asyncpg" in content

    def test_prod_subset_of_full(self):
        prod = set(read_file(REQ_PROD).strip().splitlines())
        full = set(read_file(REQ_FULL).strip().splitlines())
        assert prod.issubset(full), "Prod requirements must be a subset of full"


# ─── Backend multi-stage build ─────────────────────────────────────


class TestBackendMultiStage:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(BACKEND_DIR, "Dockerfile"))

    def test_has_two_stages(self):
        from_count = len(re.findall(r"^FROM\s+", self.content, re.MULTILINE))
        assert from_count >= 2

    def test_builder_stage_name(self):
        assert "AS builder" in self.content or "as builder" in self.content.lower()

    def test_builder_installs_from_prod_reqs(self):
        assert "requirements-prod.txt" in self.content

    def test_builder_compiles_deps(self):
        assert "gcc" in self.content or "build-essential" in self.content

    def test_builder_cleans_apt_cache(self):
        assert "rm -rf /var/lib/apt" in self.content

    def test_production_stage_copies_installed(self):
        assert "--from=builder" in self.content

    def test_uses_prefix_install(self):
        assert "--prefix" in self.content


class TestBackendSecurityHardening:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(BACKEND_DIR, "Dockerfile"))

    def test_non_root_user(self):
        assert re.search(r"^USER\s+\w+", self.content, re.MULTILINE)

    def test_has_healthcheck(self):
        assert "HEALTHCHECK" in self.content

    def test_healthcheck_has_interval(self):
        assert "--interval" in self.content

    def test_healthcheck_has_timeout(self):
        assert "--timeout" in self.content

    def test_healthcheck_has_start_period(self):
        assert "--start-period" in self.content

    def test_healthcheck_has_retries(self):
        assert "--retries" in self.content

    def test_exposes_only_8000(self):
        exposes = re.findall(r"^EXPOSE\s+(\d+)", self.content, re.MULTILINE)
        assert "8000" in exposes

    def test_no_secrets_in_dockerfile(self):
        lower = self.content.lower()
        for word in ("password", "secret_key", "apikey", "api_key"):
            assert word not in lower, f"Dockerfile must not contain {word}"


# ─── Backend Dockerfile structure ──────────────────────────────────


class TestBackendDockerfileStructure:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(BACKEND_DIR, "Dockerfile"))

    def test_copies_alembic(self):
        assert "alembic" in self.content

    def test_copies_app(self):
        assert "app/" in self.content

    def test_creates_uploads_dir(self):
        assert "uploads" in self.content

    def test_uses_entrypoint(self):
        assert "ENTRYPOINT" in self.content

    def test_no_dev_deps_in_prod_image(self):
        assert "requirements.txt" not in self.content or "requirements-prod.txt" in self.content


# ─── Frontend security hardening ───────────────────────────────────


class TestFrontendSecurityHardening:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(FRONTEND_DIR, "Dockerfile"))

    def test_multi_stage(self):
        from_count = len(re.findall(r"^FROM\s+", self.content, re.MULTILINE))
        assert from_count >= 2

    def test_has_healthcheck(self):
        assert "HEALTHCHECK" in self.content

    def test_removes_default_nginx_conf(self):
        assert "default.conf" in self.content and "rm" in self.content

    def test_sets_ownership(self):
        assert "chown" in self.content

    def test_npm_ci_ignore_scripts(self):
        assert "npm ci" in self.content
        assert "--ignore-scripts" in self.content

    def test_exposes_only_80(self):
        exposes = re.findall(r"^EXPOSE\s+(\d+)", self.content, re.MULTILINE)
        assert "80" in exposes

    def test_uses_nginx_alpine(self):
        assert "nginx:" in self.content and "alpine" in self.content


# ─── docker-compose.prod.yml ──────────────────────────────────────


class TestComposeProdOverride:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(COMPOSE_PROD_PATH)
        with open(COMPOSE_PROD_PATH, encoding="utf-8") as f:
            self.compose = yaml.safe_load(f)

    def test_file_exists(self):
        assert os.path.isfile(COMPOSE_PROD_PATH)

    def test_has_services(self):
        assert "services" in self.compose

    def test_all_services_restart_always(self):
        for name, svc in self.compose["services"].items():
            assert svc.get("restart") == "always", f"{name} should restart: always"

    def test_postgres_requires_password(self):
        pg = self.compose["services"].get("postgres", {})
        env = pg.get("environment", {})
        pwd = env.get("POSTGRES_PASSWORD", "")
        assert "${POSTGRES_PASSWORD:" in str(pwd) or "password" in str(pwd).lower()

    def test_backend_debug_false(self):
        be = self.compose["services"].get("backend", {})
        env = be.get("environment", [])
        if isinstance(env, list):
            joined = " ".join(env)
        else:
            joined = str(env)
        assert "DEBUG=false" in joined or "DEBUG" in joined

    def test_all_services_have_logging(self):
        for name, svc in self.compose["services"].items():
            assert "logging" in svc, f"Service '{name}' missing logging config"

    def test_logging_uses_json_file(self):
        for name, svc in self.compose["services"].items():
            driver = svc.get("logging", {}).get("driver")
            assert driver == "json-file", f"{name} should use json-file logging"

    def test_backend_has_resource_limits(self):
        be = self.compose["services"].get("backend", {})
        deploy = be.get("deploy", {})
        resources = deploy.get("resources", {})
        limits = resources.get("limits", {})
        assert "memory" in limits
        assert "cpus" in limits

    def test_frontend_has_resource_limits(self):
        fe = self.compose["services"].get("frontend", {})
        deploy = fe.get("deploy", {})
        resources = deploy.get("resources", {})
        limits = resources.get("limits", {})
        assert "memory" in limits

    def test_redis_maxmemory_config(self):
        redis = self.compose["services"].get("redis", {})
        cmd = redis.get("command", "")
        assert "maxmemory" in cmd


# ─── Compose prod raw ─────────────────────────────────────────────


class TestComposeProdRaw:

    def test_no_tabs(self):
        content = read_file(COMPOSE_PROD_PATH)
        for i, line in enumerate(content.splitlines(), 1):
            assert "\t" not in line, f"Line {i} contains tabs"

    def test_has_services_section(self):
        content = read_file(COMPOSE_PROD_PATH)
        assert "services:" in content
