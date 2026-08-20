"""
Logging & monitoring tests — lesson 73.
Validates structured logging, logrotate, health checks, monitoring.
"""
import os
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEPLOY_DIR = os.path.join(PROJECT_ROOT, "deploy")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─── File existence ────────────────────────────────────────────────


class TestLoggingFiles:

    def test_logging_script_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "logging.sh"))

    def test_health_check_full_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "health-check-full.sh"))


# ─── Logging script ───────────────────────────────────────────────


class TestLoggingScript:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "logging.sh"))

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_creates_log_dirs(self):
        assert "mkdir" in self.content

    def test_configures_logrotate(self):
        assert "logrotate" in self.content

    def test_logrotate_daily(self):
        assert "daily" in self.content

    def test_logrotate_compress(self):
        assert "compress" in self.content

    def test_logrotate_rotate(self):
        assert "rotate" in self.content

    def test_configures_nginx_logs(self):
        assert "nginx" in self.content.lower()

    def test_configures_journald(self):
        assert "journald" in self.content

    def test_journald_max_use(self):
        assert "SystemMaxUse" in self.content

    def test_journald_retention(self):
        assert "MaxRetentionSec" in self.content

    def test_has_output(self):
        assert "Logging" in self.content

    def test_sets_permissions(self):
        assert "chown" in self.content or "chmod" in self.content


# ─── Health check full script ─────────────────────────────────────


class TestHealthCheckFull:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "health-check-full.sh"))

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_checks_backend_api(self):
        assert "backend" in self.content.lower() or "api" in self.content.lower()

    def test_checks_postgres(self):
        assert "postgres" in self.content.lower()

    def test_checks_redis(self):
        assert "redis" in self.content.lower()

    def test_checks_frontend(self):
        assert "frontend" in self.content.lower()

    def test_checks_nginx(self):
        assert "nginx" in self.content.lower()

    def test_checks_docker_containers(self):
        assert "docker" in self.content.lower()

    def test_checks_disk_space(self):
        assert "df" in self.content or "disk" in self.content.lower()

    def test_uses_curl(self):
        assert "curl" in self.content

    def test_uses_psql(self):
        assert "pg_isready" in self.content or "psql" in self.content

    def test_uses_redis_cli(self):
        assert "redis-cli" in self.content

    def test_has_healthy_flag(self):
        assert "HEALTHY" in self.content

    def test_has_exit_on_failure(self):
        assert "exit 1" in self.content

    def test_checks_multiple_services(self):
        assert "postgres" in self.content.lower()
        assert "redis" in self.content.lower()

    def test_warns_on_disk_usage(self):
        assert "WARNING" in self.content or "CRITICAL" in self.content


# ─── Script raw ───────────────────────────────────────────────────


class TestLoggingScriptsRaw:

    @pytest.mark.parametrize("filename", [
        "logging.sh",
        "health-check-full.sh",
    ])
    def test_has_shebang(self, filename):
        content = read_file(os.path.join(DEPLOY_DIR, filename))
        assert content.startswith("#!/bin/bash")

    @pytest.mark.parametrize("filename", [
        "logging.sh",
        "health-check-full.sh",
    ])
    def test_set_euo_pipefail(self, filename):
        content = read_file(os.path.join(DEPLOY_DIR, filename))
        assert "set -euo pipefail" in content

    @pytest.mark.parametrize("filename", [
        "logging.sh",
        "health-check-full.sh",
    ])
    def test_no_tabs(self, filename):
        content = read_file(os.path.join(DEPLOY_DIR, filename))
        for i, line in enumerate(content.splitlines(), 1):
            if line.strip() and not line.strip().startswith("#"):
                assert "\t" not in line, f"{filename}:{i} contains tabs"

    @pytest.mark.parametrize("filename", [
        "logging.sh",
        "health-check-full.sh",
    ])
    def test_has_header(self, filename):
        content = read_file(os.path.join(DEPLOY_DIR, filename))
        assert "InternetShop" in content
