"""
Production PostgreSQL / Redis tests — lesson 70.
Validates DB configs, persistence, monitoring, tuning, docker-compose integration.
"""
import os
import re
import pytest
import yaml


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEPLOY_DIR = os.path.join(PROJECT_ROOT, "deploy")
COMPOSE_PATH = os.path.join(PROJECT_ROOT, "docker-compose.yml")
COMPOSE_PROD_PATH = os.path.join(PROJECT_ROOT, "docker-compose.prod.yml")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─── File existence ────────────────────────────────────────────────


class TestProductionDBFiles:

    def test_postgres_conf_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "postgres-prod.conf"))

    def test_redis_conf_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "redis-prod.conf"))

    def test_monitor_db_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "monitor-db.sh"))

    def test_compose_prod_exists(self):
        assert os.path.isfile(COMPOSE_PROD_PATH)


# ─── PostgreSQL production config ─────────────────────────────────


class TestPostgresProdConfig:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "postgres-prod.conf"))

    def test_listen_addresses(self):
        assert "listen_addresses" in self.content

    def test_max_connections(self):
        assert "max_connections" in self.content
        match = re.search(r"max_connections\s*=\s*(\d+)", self.content)
        assert match is not None
        assert int(match.group(1)) >= 50

    def test_shared_buffers(self):
        assert "shared_buffers" in self.content

    def test_effective_cache_size(self):
        assert "effective_cache_size" in self.content

    def test_work_mem(self):
        assert "work_mem" in self.content

    def test_maintenance_work_mem(self):
        assert "maintenance_work_mem" in self.content

    def test_wal_buffers(self):
        assert "wal_buffers" in self.content

    def test_checkpoint_completion_target(self):
        assert "checkpoint_completion_target" in self.content

    def test_random_page_cost(self):
        assert "random_page_cost" in self.content

    def test_effective_io_concurrency(self):
        assert "effective_io_concurrency" in self.content

    def test_logging_collector_on(self):
        assert "logging_collector = on" in self.content

    def test_log_min_duration(self):
        assert "log_min_duration_statement" in self.content

    def test_log_checkpoints(self):
        assert "log_checkpoints = on" in self.content

    def test_log_connections(self):
        assert "log_connections = on" in self.content

    def test_log_disconnections(self):
        assert "log_disconnections = on" in self.content

    def test_log_lock_waits(self):
        assert "log_lock_waits = on" in self.content

    def test_autovacuum_on(self):
        assert "autovacuum = on" in self.content

    def test_timezone_utc(self):
        assert "timezone = 'UTC'" in self.content

    def test_wal_size(self):
        assert "min_wal_size" in self.content
        assert "max_wal_size" in self.content


# ─── Redis production config ───────────────────────────────────────


class TestRedisProdConfig:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "redis-prod.conf"))

    def test_bind_address(self):
        assert "bind" in self.content

    def test_port(self):
        assert "port 6379" in self.content

    def test_maxmemory(self):
        assert "maxmemory" in self.content

    def test_maxmemory_policy(self):
        assert "maxmemory-policy" in self.content

    def test_lru_eviction(self):
        assert "allkeys-lru" in self.content

    def test_rdb_save_enabled(self):
        assert "save" in self.content

    def test_multiple_save_rules(self):
        save_lines = [l for l in self.content.splitlines() if l.strip().startswith("save ")]
        assert len(save_lines) >= 3

    def test_aof_enabled(self):
        assert "appendonly yes" in self.content

    def test_aof_sync(self):
        assert "appendfsync" in self.content

    def test_aof_rewrite(self):
        assert "auto-aof-rewrite" in self.content

    def test_loglevel(self):
        assert "loglevel" in self.content

    def test_slow_log(self):
        assert "slowlog" in self.content

    def test_tcp_keepalive(self):
        assert "tcp-keepalive" in self.content

    def test_timeout(self):
        assert "timeout" in self.content

    def test_protected_mode(self):
        assert "protected-mode" in self.content


# ─── Monitor script ────────────────────────────────────────────────


class TestMonitorDB:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "monitor-db.sh"))

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

    def test_checks_redis_memory(self):
        assert "info memory" in self.content or "memory" in self.content.lower()

    def test_uses_docker_compose(self):
        assert "docker compose" in self.content

    def test_warns_on_high_connections(self):
        assert "WARNING" in self.content


# ─── Docker Compose prod — DB config mounting ─────────────────────


class TestComposeProdDB:

    @pytest.fixture(autouse=True)
    def load(self):
        with open(COMPOSE_PROD_PATH, encoding="utf-8") as f:
            self.compose = yaml.safe_load(f)

    def test_postgres_has_custom_config(self):
        pg = self.compose["services"].get("postgres", {})
        cmd = pg.get("command", "")
        assert "config_file" in cmd or "postgresql.conf" in cmd

    def test_postgres_mounts_config(self):
        pg = self.compose["services"].get("postgres", {})
        vols = pg.get("volumes", [])
        assert any("postgres-prod.conf" in v for v in vols)

    def test_redis_has_custom_config(self):
        redis = self.compose["services"].get("redis", {})
        cmd = redis.get("command", "")
        assert "redis.conf" in cmd

    def test_redis_mounts_config(self):
        redis = self.compose["services"].get("redis", {})
        vols = redis.get("volumes", [])
        assert any("redis-prod.conf" in v for v in vols)

    def test_postgres_config_readonly(self):
        pg = self.compose["services"].get("postgres", {})
        vols = pg.get("volumes", [])
        config_vols = [v for v in vols if "postgres-prod.conf" in v]
        assert any(":ro" in v for v in config_vols)

    def test_redis_config_readonly(self):
        redis = self.compose["services"].get("redis", {})
        vols = redis.get("volumes", [])
        config_vols = [v for v in vols if "redis-prod.conf" in v]
        assert any(":ro" in v for v in config_vols)

    def test_postgres_persistence_volume(self):
        pg = self.compose["services"].get("postgres", {})
        vols = pg.get("volumes", [])
        assert any("pgdata" in v for v in vols)

    def test_redis_persistence_volume(self):
        redis = self.compose["services"].get("redis", {})
        vols = redis.get("volumes", [])
        assert any("redisdata" in v for v in vols)

    def test_postgres_restart_always(self):
        pg = self.compose["services"].get("postgres", {})
        assert pg.get("restart") == "always"

    def test_redis_restart_always(self):
        redis = self.compose["services"].get("redis", {})
        assert redis.get("restart") == "always"


# ─── Config content raw ───────────────────────────────────────────


class TestConfigRaw:

    def test_postgres_conf_no_tabs(self):
        content = read_file(os.path.join(DEPLOY_DIR, "postgres-prod.conf"))
        for i, line in enumerate(content.splitlines(), 1):
            if line.strip() and not line.strip().startswith("#"):
                assert "\t" not in line, f"Line {i} contains tabs"

    def test_redis_conf_no_tabs(self):
        content = read_file(os.path.join(DEPLOY_DIR, "redis-prod.conf"))
        for i, line in enumerate(content.splitlines(), 1):
            if line.strip() and not line.strip().startswith("#"):
                assert "\t" not in line, f"Line {i} contains tabs"

    def test_postgres_conf_has_key_settings(self):
        content = read_file(os.path.join(DEPLOY_DIR, "postgres-prod.conf"))
        for key in ("shared_buffers", "work_mem", "wal_buffers", "max_connections"):
            assert key in content

    def test_redis_conf_has_key_settings(self):
        content = read_file(os.path.join(DEPLOY_DIR, "redis-prod.conf"))
        for key in ("maxmemory", "appendonly", "save", "timeout"):
            assert key in content
