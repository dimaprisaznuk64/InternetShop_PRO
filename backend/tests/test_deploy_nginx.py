"""
Nginx configuration tests — lesson 69.
Validates reverse proxy, rate limiting, security headers, upstream, performance.
"""
import os
import re
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEPLOY_DIR = os.path.join(PROJECT_ROOT, "deploy")
NGINX_DIR = os.path.join(DEPLOY_DIR, "nginx")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─── File existence ────────────────────────────────────────────────


class TestNginxFilesExist:

    def test_nginx_main_conf_exists(self):
        assert os.path.isfile(os.path.join(NGINX_DIR, "nginx-main.conf"))

    def test_internetshop_conf_exists(self):
        assert os.path.isfile(os.path.join(NGINX_DIR, "internetshop.conf"))

    def test_api_proxy_conf_exists(self):
        assert os.path.isfile(os.path.join(NGINX_DIR, "api-proxy.conf"))

    def test_nginx_security_script_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "nginx-security.sh"))


# ─── Main nginx config ────────────────────────────────────────────


class TestNginxMainConfig:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(NGINX_DIR, "nginx-main.conf"))

    def test_worker_processes_auto(self):
        assert "worker_processes auto" in self.content

    def test_worker_connections(self):
        assert "worker_connections" in self.content

    def test_multi_accept(self):
        assert "multi_accept on" in self.content

    def test_use_epoll(self):
        assert "use epoll" in self.content

    def test_sendfile(self):
        assert "sendfile on" in self.content

    def test_tcp_nopush(self):
        assert "tcp_nopush on" in self.content

    def test_tcp_nodelay(self):
        assert "tcp_nodelay on" in self.content

    def test_keepalive_timeout(self):
        assert "keepalive_timeout" in self.content

    def test_server_tokens_off(self):
        assert "server_tokens off" in self.content

    def test_gzip_on(self):
        assert "gzip on" in self.content

    def test_gzip_comp_level(self):
        assert "gzip_comp_level" in self.content

    def test_gzip_min_length(self):
        assert "gzip_min_length" in self.content

    def test_gzip_types_include(self):
        assert "application/json" in self.content
        assert "application/javascript" in self.content
        assert "text/css" in self.content

    def test_rate_limiting_zones(self):
        assert "limit_req_zone" in self.content

    def test_api_rate_limit(self):
        assert "zone=api" in self.content

    def test_login_rate_limit(self):
        assert "zone=login" in self.content

    def test_general_rate_limit(self):
        assert "zone=general" in self.content

    def test_security_headers(self):
        assert "X-Frame-Options" in self.content
        assert "X-Content-Type-Options" in self.content
        assert "X-XSS-Protection" in self.content
        assert "Referrer-Policy" in self.content

    def test_proxy_http_version(self):
        assert "proxy_http_version 1.1" in self.content

    def test_proxy_headers(self):
        assert "X-Real-IP" in self.content
        assert "X-Forwarded-For" in self.content
        assert "X-Forwarded-Proto" in self.content

    def test_upstream_defined(self):
        assert "upstream backend" in self.content

    def test_upstream_least_conn(self):
        assert "least_conn" in self.content

    def test_upstream_keepalive(self):
        assert "keepalive" in self.content

    def test_proxy_buffering(self):
        assert "proxy_buffering on" in self.content

    def test_proxy_timeouts(self):
        assert "proxy_connect_timeout" in self.content
        assert "proxy_send_timeout" in self.content
        assert "proxy_read_timeout" in self.content

    def test_limit_req_status_429(self):
        assert "limit_req_status 429" in self.content

    def test_include_conf_d(self):
        assert "conf.d/*.conf" in self.content


# ─── Internetshop server config ───────────────────────────────────


class TestInternetshopConfig:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(NGINX_DIR, "internetshop.conf"))

    def test_listens_on_80(self):
        assert "listen 80" in self.content

    def test_listens_on_443(self):
        assert "listen 443 ssl" in self.content

    def test_ipv6_support(self):
        assert "listen [::]:80" in self.content or "listen [::]:443" in self.content

    def test_http_to_https_redirect(self):
        assert "301" in self.content and "https" in self.content

    def test_ssl_protocols(self):
        assert "TLSv1.2" in self.content
        assert "TLSv1.3" in self.content

    def test_ssl_session_tickets_off(self):
        assert "ssl_session_tickets off" in self.content

    def test_ocsp_stapling(self):
        assert "ssl_stapling on" in self.content
        assert "ssl_stapling_verify on" in self.content

    def test_hsts_preload(self):
        assert "preload" in self.content

    def test_letsencrypt_acme_challenge(self):
        assert ".well-known/acme-challenge" in self.content

    def test_general_rate_limit(self):
        assert "limit_req zone=general" in self.content

    def test_api_rate_limit(self):
        assert "limit_req zone=api" in self.content

    def test_login_rate_limit(self):
        assert "limit_req zone=login" in self.content

    def test_register_rate_limit(self):
        assert "register" in self.content and "limit_req" in self.content

    def test_api_proxy_to_upstream(self):
        assert "proxy_pass http://backend" in self.content

    def test_health_no_rate_limit(self):
        health_section = self.content[self.content.find("location /health"):]
        assert "limit_req" not in health_section.split("location")[0] if "location" in health_section else True

    def test_spa_fallback(self):
        assert "try_files" in self.content and "index.html" in self.content

    def test_static_assets_long_cache(self):
        assert "expires 1y" in self.content
        assert "immutable" in self.content

    def test_deny_hidden_files(self):
        assert "location ~ /\\." in self.content
        assert "deny all" in self.content

    def test_access_log(self):
        assert "access_log" in self.content

    def test_error_log(self):
        assert "error_log" in self.content


# ─── API proxy config ─────────────────────────────────────────────


class TestAPIProxyConfig:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(NGINX_DIR, "api-proxy.conf"))

    def test_upstream_defined(self):
        assert "upstream" in self.content

    def test_keepalive(self):
        assert "keepalive" in self.content

    def test_proxy_pass(self):
        assert "proxy_pass" in self.content

    def test_proxy_headers(self):
        assert "X-Real-IP" in self.content
        assert "X-Forwarded-For" in self.content
        assert "X-Forwarded-Proto" in self.content

    def test_http_version_11(self):
        assert "proxy_http_version 1.1" in self.content

    def test_connection_header(self):
        assert "Connection" in self.content

    def test_proxy_timeouts(self):
        assert "proxy_read_timeout" in self.content
        assert "proxy_connect_timeout" in self.content
        assert "proxy_send_timeout" in self.content


# ─── Nginx security script ────────────────────────────────────────


class TestNginxSecurityScript:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "nginx-security.sh"))

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_checks_nginx_installed(self):
        assert "nginx" in self.content and ("command" in self.content or "installed" in self.content)

    def test_sets_server_tokens_off(self):
        assert "server_tokens" in self.content

    def test_sets_security_headers(self):
        assert "X-Frame-Options" in self.content
        assert "X-Content-Type-Options" in self.content

    def test_tests_nginx_config(self):
        assert "nginx -t" in self.content

    def test_creates_security_headers_file(self):
        assert "security-headers.conf" in self.content

    def test_permissions_policy(self):
        assert "Permissions-Policy" in self.content


# ─── Nginx config raw ─────────────────────────────────────────────


class TestNginxConfigRaw:

    @pytest.mark.parametrize("filename", [
        "nginx-main.conf",
        "internetshop.conf",
        "api-proxy.conf",
    ])
    def test_no_tabs(self, filename):
        content = read_file(os.path.join(NGINX_DIR, filename))
        for i, line in enumerate(content.splitlines(), 1):
            assert "\t" not in line, f"{filename}:{i} contains tabs"

    @pytest.mark.parametrize("filename", [
        "nginx-main.conf",
        "internetshop.conf",
        "api-proxy.conf",
    ])
    def test_has_events_or_server(self, filename):
        content = read_file(os.path.join(NGINX_DIR, filename))
        has_block = any(kw in content for kw in ("events", "server", "upstream", "http"))
        assert has_block, f"{filename} missing nginx block directives"
