"""
Backend deploy tests — lesson 66.
Validates deploy scripts, backup, health check, production config.
"""
import os
import re
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEPLOY_DIR = os.path.join(PROJECT_ROOT, "deploy")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_script(name: str) -> str:
    return read_file(os.path.join(DEPLOY_DIR, name))


# ─── File existence ────────────────────────────────────────────────


class TestBackendDeployFiles:

    def test_deploy_backend_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "deploy-backend.sh"))

    def test_backup_db_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "backup-db.sh"))

    def test_health_check_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "health-check.sh"))

    def test_env_prod_example_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, ".env.prod.example"))


# ─── Deploy backend script ────────────────────────────────────────


class TestDeployBackend:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("deploy-backend.sh")

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_pulls_latest_code(self):
        assert "git pull" in self.content

    def test_builds_docker_image(self):
        assert "docker compose" in self.content and "build" in self.content

    def test_runs_migrations(self):
        assert "alembic" in self.content and "upgrade" in self.content

    def test_restarts_services(self):
        assert "up -d" in self.content

    def test_checks_env_file(self):
        assert ".env.docker" in self.content

    def test_health_check_loop(self):
        assert "healthy" in self.content and "while" in self.content

    def test_max_wait_timeout(self):
        assert "MAX_WAIT" in self.content

    def test_shows_logs_on_failure(self):
        assert "logs" in self.content

    def test_uses_prod_compose(self):
        assert "docker-compose.prod" in self.content or "docker-compose.prod.yml" in self.content


# ─── Backup database script ────────────────────────────────────────


class TestBackupDB:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("backup-db.sh")

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_creates_backup_dir(self):
        assert "mkdir" in self.content

    def test_uses_pg_dump(self):
        assert "pg_dump" in self.content

    def test_compresses_backup(self):
        assert "gzip" in self.content

    def test_verifies_backup(self):
        assert "-s" in self.content and "BACKUP_FILE" in self.content

    def test_cleans_old_backups(self):
        assert "rm" in self.content and "tail" in self.content

    def test_keeps_last_7(self):
        assert "7" in self.content

    def test_uses_docker_compose_exec(self):
        assert "docker compose exec" in self.content

    def test_timestamp_in_filename(self):
        assert "DATE" in self.content and "date" in self.content


# ─── Health check script ──────────────────────────────────────────


class TestHealthCheck:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("health-check.sh")

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_checks_backend(self):
        assert "backend" in self.content.lower()

    def test_checks_frontend(self):
        assert "frontend" in self.content.lower()

    def test_checks_docker_services(self):
        assert "docker compose" in self.content

    def test_uses_curl(self):
        assert "curl" in self.content

    def test_counts_failures(self):
        assert "FAILURES" in self.content

    def test_exits_on_failure(self):
        assert "exit 1" in self.content

    def test_configurable_urls(self):
        assert "BACKEND_URL" in self.content
        assert "FRONTEND_URL" in self.content


# ─── .env.prod.example ────────────────────────────────────────────


class TestEnvProdExample:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, ".env.prod.example"))

    def test_has_database_url(self):
        assert "DATABASE_URL" in self.content

    def test_has_secret_key(self):
        assert "SECRET_KEY" in self.content

    def test_has_redis_url(self):
        assert "REDIS_URL" in self.content

    def test_has_debug_false(self):
        assert "DEBUG=false" in self.content

    def test_has_cors_origins(self):
        assert "CORS_ORIGINS" in self.content

    def test_has_allowed_hosts(self):
        assert "ALLOWED_HOSTS" in self.content

    def test_postgres_password_placeholder(self):
        assert "CHANGE_ME" in self.content

    def test_uses_postgres_service_host(self):
        assert "postgres:" in self.content

    def test_uses_redis_service_host(self):
        assert "redis:" in self.content

    def test_debug_is_false(self):
        for line in self.content.splitlines():
            if line.strip().startswith("DEBUG="):
                assert line.strip() == "DEBUG=false"


# ─── Script standards ─────────────────────────────────────────────


class TestBackendDeployScriptStandards:

    @pytest.mark.parametrize("script", [
        "deploy-backend.sh",
        "backup-db.sh",
        "health-check.sh",
    ])
    def test_has_shebang(self, script):
        content = read_script(script)
        assert content.startswith("#!/bin/bash")

    @pytest.mark.parametrize("script", [
        "deploy-backend.sh",
        "backup-db.sh",
        "health-check.sh",
    ])
    def test_set_e(self, script):
        content = read_script(script)
        assert "set -e" in content

    @pytest.mark.parametrize("script", [
        "deploy-backend.sh",
        "backup-db.sh",
        "health-check.sh",
    ])
    def test_uses_docker_compose(self, script):
        content = read_script(script)
        assert "docker compose" in content


# ─── Integration: deploy + docker-compose consistency ──────────────


class TestDeployConsistency:

    def test_prod_compose_has_backend_service(self):
        compose_prod = read_file(os.path.join(PROJECT_ROOT, "docker-compose.prod.yml"))
        assert "backend:" in compose_prod

    def test_deploy_script_references_prod_compose(self):
        deploy = read_script("deploy-backend.sh")
        assert "prod" in deploy.lower() or "production" in deploy.lower()

    def test_env_prod_matches_env_docker_structure(self):
        env_prod = read_file(os.path.join(DEPLOY_DIR, ".env.prod.example"))
        env_docker = read_file(os.path.join(PROJECT_ROOT, ".env.docker"))
        prod_keys = {line.split("=")[0].strip() for line in env_prod.splitlines() if "=" in line and not line.strip().startswith("#")}
        docker_keys = {line.split("=")[0].strip() for line in env_docker.splitlines() if "=" in line and not line.strip().startswith("#")}
        assert prod_keys == docker_keys, f"Mismatched keys: {prod_keys.symmetric_difference(docker_keys)}"
