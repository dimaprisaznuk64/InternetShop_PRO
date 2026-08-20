"""
Performance tests — lesson 72.
Validates performance check scripts, SQL audit queries, monitoring.
"""
import os
import re
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEPLOY_DIR = os.path.join(PROJECT_ROOT, "deploy")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─── File existence ────────────────────────────────────────────────


class TestPerformanceFiles:

    def test_performance_check_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "performance-check.sh"))

    def test_db_performance_sql_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "db-performance.sql"))


# ─── Performance check script ─────────────────────────────────────


class TestPerformanceCheck:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "performance-check.sh"))

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_checks_api_response_time(self):
        assert "curl" in self.content

    def test_checks_api_endpoints(self):
        assert "/health" in self.content or "/docs" in self.content

    def test_checks_cache_hit_ratio(self):
        assert "blks_hit" in self.content or "cache" in self.content.lower()

    def test_checks_slow_queries(self):
        assert "slow" in self.content.lower() or "pg_stat_activity" in self.content

    def test_checks_table_bloat(self):
        assert "dead_tup" in self.content or "bloat" in self.content.lower()

    def test_checks_redis_hit_rate(self):
        assert "keyspace" in self.content or "hit" in self.content.lower()

    def test_checks_docker_stats(self):
        assert "docker stats" in self.content

    def test_warns_on_low_cache(self):
        assert "WARNING" in self.content

    def test_uses_docker_compose(self):
        assert "docker compose" in self.content

    def test_uses_psql(self):
        assert "psql" in self.content

    def test_has_header(self):
        assert "Performance" in self.content

    def test_has_footer(self):
        assert "complete" in self.content.lower()


# ─── DB performance SQL ───────────────────────────────────────────


class TestDBPerformanceSQL:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "db-performance.sql"))

    def test_queries_index_usage(self):
        assert "idx_scan" in self.content

    def test_queries_unused_indexes(self):
        assert "pg_stat_user_indexes" in self.content

    def test_queries_table_bloat(self):
        assert "n_dead_tup" in self.content

    def test_queries_slow_queries(self):
        assert "pg_stat_statements" in self.content

    def test_queries_table_sizes(self):
        assert "pg_total_relation_size" in self.content

    def test_queries_cache_hit_ratio(self):
        assert "blks_hit" in self.content

    def test_queries_connection_stats(self):
        assert "pg_stat_activity" in self.content

    def test_queries_long_running(self):
        assert "duration" in self.content

    def test_orders_by_seq_scan(self):
        assert "ORDER BY seq_scan" in self.content

    def test_orders_by_dead_tup(self):
        assert "ORDER BY n_dead_tup" in self.content

    def test_orders_by_mean_time(self):
        assert "ORDER BY mean_exec_time" in self.content

    def test_has_limits(self):
        assert "LIMIT 10" in self.content or "LIMIT 5" in self.content

    def test_has_echo_headers(self):
        assert "\\echo" in self.content

    def test_detects_needs_index(self):
        assert "NEEDS INDEX" in self.content

    def test_detects_needs_vacuum(self):
        assert "NEEDS VACUUM" in self.content


# ─── Script raw ───────────────────────────────────────────────────


class TestPerformanceScriptsRaw:

    def test_shell_script_has_shebang(self):
        content = read_file(os.path.join(DEPLOY_DIR, "performance-check.sh"))
        assert content.startswith("#!/bin/bash")

    def test_shell_script_no_tabs(self):
        content = read_file(os.path.join(DEPLOY_DIR, "performance-check.sh"))
        for i, line in enumerate(content.splitlines(), 1):
            if line.strip() and not line.strip().startswith("#"):
                assert "\t" not in line, f"Line {i} contains tabs"

    def test_sql_has_select(self):
        content = read_file(os.path.join(DEPLOY_DIR, "db-performance.sql"))
        assert "SELECT" in content

    def test_sql_queries_pg_stat(self):
        content = read_file(os.path.join(DEPLOY_DIR, "db-performance.sql"))
        assert "pg_stat_" in content
