"""
Production audit tests — lesson 71.
Validates audit scripts (security, database, full audit).
"""
import os
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEPLOY_DIR = os.path.join(PROJECT_ROOT, "deploy")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─── File existence ────────────────────────────────────────────────


class TestAuditFiles:

    def test_audit_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "audit.sh"))

    def test_audit_security_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "audit-security.sh"))

    def test_audit_db_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "audit-db.sh"))


# ─── Audit security script ────────────────────────────────────────


class TestAuditSecurity:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "audit-security.sh"))

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_checks_ssh(self):
        assert "sshd" in self.content.lower() or "ssh" in self.content.lower()

    def test_checks_root_login(self):
        assert "PermitRootLogin" in self.content

    def test_checks_password_auth(self):
        assert "PasswordAuthentication" in self.content

    def test_checks_firewall(self):
        assert "ufw" in self.content.lower() or "firewall" in self.content.lower()

    def test_checks_open_ports(self):
        assert "ss -tlnp" in self.content or "netstat" in self.content

    def test_checks_docker_secrets(self):
        assert "secret" in self.content.lower() or "password" in self.content.lower()

    def test_checks_env_files(self):
        assert ".env" in self.content

    def test_checks_failed_logins(self):
        assert "Failed" in self.content or "failed" in self.content

    def test_has_issue_counter(self):
        assert "ISSUES" in self.content

    def test_warns_on_issues(self):
        assert "WARNING" in self.content

    def test_uses_apt(self):
        assert "apt" in self.content

    def test_checks_auth_log(self):
        assert "auth.log" in self.content or "secure" in self.content


# ─── Audit DB script ──────────────────────────────────────────────


class TestAuditDB:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "audit-db.sh"))

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_checks_postgres(self):
        assert "postgres" in self.content.lower()

    def test_checks_redis(self):
        assert "redis" in self.content.lower()

    def test_checks_connections(self):
        assert "pg_stat_activity" in self.content or "connections" in self.content.lower()

    def test_checks_database_size(self):
        assert "pg_database_size" in self.content or "size" in self.content.lower()

    def test_checks_table_sizes(self):
        assert "pg_total_relation_size" in self.content or "table" in self.content.lower()

    def test_checks_bloat(self):
        assert "dead_tup" in self.content or "bloat" in self.content.lower()

    def test_checks_missing_indexes(self):
        assert "seq_scan" in self.content or "index" in self.content.lower()

    def test_checks_redis_memory(self):
        assert "info memory" in self.content or "memory" in self.content.lower()

    def test_checks_redis_keys(self):
        assert "dbsize" in self.content or "keys" in self.content.lower()

    def test_uses_docker_compose(self):
        assert "docker compose" in self.content

    def test_uses_psql(self):
        assert "psql" in self.content


# ─── Full audit script ────────────────────────────────────────────


class TestAuditFull:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "audit.sh"))

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_runs_security_audit(self):
        assert "audit-security" in self.content

    def test_runs_db_audit(self):
        assert "audit-db" in self.content

    def test_checks_disk(self):
        assert "df" in self.content

    def test_checks_memory(self):
        assert "free" in self.content

    def test_checks_uptime(self):
        assert "uptime" in self.content

    def test_checks_docker(self):
        assert "docker compose" in self.content

    def test_shows_hostname(self):
        assert "hostname" in self.content

    def test_shows_date(self):
        assert "date" in self.content

    def test_has_error_counter(self):
        assert "ERRORS" in self.content or "ERROR" in self.content

    def test_has_header(self):
        assert "InternetShop PRO" in self.content


# ─── Script raw ───────────────────────────────────────────────────


class TestAuditScriptsRaw:

    @pytest.mark.parametrize("filename", [
        "audit.sh",
        "audit-security.sh",
        "audit-db.sh",
    ])
    def test_has_shebang(self, filename):
        content = read_file(os.path.join(DEPLOY_DIR, filename))
        assert content.startswith("#!/bin/bash")

    @pytest.mark.parametrize("filename", [
        "audit.sh",
        "audit-security.sh",
        "audit-db.sh",
    ])
    def test_set_euo_pipefail(self, filename):
        content = read_file(os.path.join(DEPLOY_DIR, filename))
        assert "set -euo pipefail" in content

    @pytest.mark.parametrize("filename", [
        "audit.sh",
        "audit-security.sh",
        "audit-db.sh",
    ])
    def test_no_tabs(self, filename):
        content = read_file(os.path.join(DEPLOY_DIR, filename))
        for i, line in enumerate(content.splitlines(), 1):
            if line.strip() and not line.strip().startswith("#"):
                assert "\t" not in line, f"{filename}:{i} contains tabs"

    @pytest.mark.parametrize("filename", [
        "audit.sh",
        "audit-security.sh",
        "audit-db.sh",
    ])
    def test_has_output_header(self, filename):
        content = read_file(os.path.join(DEPLOY_DIR, filename))
        assert "InternetShop" in content or "audit" in content.lower()
