"""
Frontend deploy tests — lesson 67.
Validates frontend deployment scripts, build process, nginx config.
"""
import os
import re
import pytest
import yaml


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEPLOY_DIR = os.path.join(PROJECT_ROOT, "deploy")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
COMPOSE_PATH = os.path.join(PROJECT_ROOT, "docker-compose.yml")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_script(name: str) -> str:
    return read_file(os.path.join(DEPLOY_DIR, name))


# ─── File existence ────────────────────────────────────────────────


class TestFrontendDeployFiles:

    def test_deploy_frontend_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "deploy-frontend.sh"))

    def test_build_frontend_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "build-frontend.sh"))

    def test_nginx_internetshop_conf_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "nginx", "internetshop.conf"))

    def test_frontend_dockerfile_exists(self):
        assert os.path.isfile(os.path.join(FRONTEND_DIR, "Dockerfile"))

    def test_frontend_nginx_conf_exists(self):
        assert os.path.isfile(os.path.join(FRONTEND_DIR, "nginx.conf"))


# ─── Deploy frontend script ───────────────────────────────────────


class TestDeployFrontend:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("deploy-frontend.sh")

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_pulls_code(self):
        assert "git pull" in self.content

    def test_builds_docker_image(self):
        assert "docker compose" in self.content and "build" in self.content

    def test_builds_static_files(self):
        assert "npm run build" in self.content or "build" in self.content

    def test_creates_nginx_html_dir(self):
        assert "mkdir" in self.content

    def test_copies_nginx_config(self):
        assert "cp" in self.content and "internetshop.conf" in self.content

    def test_tests_nginx_config(self):
        assert "nginx -t" in self.content

    def test_reloads_nginx(self):
        assert "nginx" in self.content and "reload" in self.content

    def test_uses_prod_compose(self):
        assert "prod" in self.content.lower() or "production" in self.content.lower()


# ─── Build frontend script ────────────────────────────────────────


class TestBuildFrontend:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("build-frontend.sh")

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_installs_deps(self):
        assert "npm ci" in self.content

    def test_runs_tests(self):
        assert "npm test" in self.content

    def test_runs_lint(self):
        assert "npm run lint" in self.content

    def test_builds_production(self):
        assert "npm run build" in self.content

    def test_shows_build_size(self):
        assert "du -sh" in self.content

    def test_warns_on_failure(self):
        assert "WARN" in self.content


# ─── Frontend Dockerfile (re-validated for deploy context) ─────────


class TestFrontendDockerfileDeploy:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(FRONTEND_DIR, "Dockerfile"))

    def test_multi_stage(self):
        from_count = len(re.findall(r"^FROM\s+", self.content, re.MULTILINE))
        assert from_count >= 2

    def test_build_stage_uses_node(self):
        lines = [l for l in self.content.splitlines() if l.strip().upper().startswith("FROM")]
        assert any("node" in l.lower() for l in lines)

    def test_serve_stage_uses_nginx(self):
        lines = [l for l in self.content.splitlines() if l.strip().upper().startswith("FROM")]
        assert any("nginx" in l.lower() for l in lines)

    def test_npm_ci_with_ignore_scripts(self):
        assert "npm ci" in self.content and "--ignore-scripts" in self.content

    def test_copies_build_output(self):
        assert "COPY --from=build" in self.content

    def test_has_healthcheck(self):
        assert "HEALTHCHECK" in self.content

    def test_removes_default_nginx(self):
        assert "default.conf" in self.content and "rm" in self.content

    def test_sets_ownership(self):
        assert "chown" in self.content

    def test_exposes_80(self):
        exposes = re.findall(r"^EXPOSE\s+(\d+)", self.content, re.MULTILINE)
        assert "80" in exposes

    def test_uses_nginx_alpine(self):
        assert "nginx:" in self.content and "alpine" in self.content


# ─── Frontend nginx.conf (container-level) ────────────────────────


class TestFrontendNginxConf:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(FRONTEND_DIR, "nginx.conf"))

    def test_listens_on_80(self):
        assert "listen 80" in self.content

    def test_spa_fallback(self):
        assert "try_files" in self.content and "index.html" in self.content

    def test_api_proxy_to_backend(self):
        assert "proxy_pass" in self.content and "backend" in self.content

    def test_health_proxy(self):
        assert "/health" in self.content and "proxy_pass" in self.content

    def test_static_assets_caching(self):
        assert "expires" in self.content and "Cache-Control" in self.content

    def test_gzip_enabled(self):
        assert "gzip on" in self.content

    def test_gzip_types(self):
        assert "application/json" in self.content
        assert "application/javascript" in self.content

    def test_gzip_min_length(self):
        assert "gzip_min_length" in self.content

    def test_proxy_headers(self):
        assert "X-Real-IP" in self.content
        assert "X-Forwarded-For" in self.content
        assert "X-Forwarded-Proto" in self.content


# ─── Nginx production config (host-level) ─────────────────────────


class TestNginxProductionConfig:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "nginx", "internetshop.conf"))

    def test_http_to_https_redirect(self):
        assert "301" in self.content and "https" in self.content

    def test_ssl_protocols(self):
        assert "TLSv1.2" in self.content and "TLSv1.3" in self.content

    def test_hsts_header(self):
        assert "Strict-Transport-Security" in self.content

    def test_security_headers(self):
        assert "X-Frame-Options" in self.content
        assert "X-Content-Type-Options" in self.content
        assert "X-XSS-Protection" in self.content
        assert "Referrer-Policy" in self.content

    def test_letsencrypt_cert_path(self):
        assert "letsencrypt" in self.content.lower()

    def test_api_proxy(self):
        assert "/api/" in self.content and "proxy_pass" in self.content

    def test_health_proxy(self):
        assert "/health" in self.content and "proxy_pass" in self.content

    def test_spa_fallback(self):
        assert "try_files" in self.content and "index.html" in self.content

    def test_gzip(self):
        assert "gzip on" in self.content

    def test_logs_configured(self):
        assert "access_log" in self.content
        assert "error_log" in self.content

    def test_upstream_timeout(self):
        assert "proxy_read_timeout" in self.content
        assert "proxy_connect_timeout" in self.content


# ─── Compose frontend service ─────────────────────────────────────


class TestComposeFrontendService:

    @pytest.fixture(autouse=True)
    def load(self):
        with open(COMPOSE_PATH, encoding="utf-8") as f:
            self.compose = yaml.safe_load(f)

    def test_frontend_service_exists(self):
        assert "frontend" in self.compose["services"]

    def test_frontend_depends_on_backend(self):
        deps = self.compose["services"]["frontend"].get("depends_on", {})
        assert "backend" in deps

    def test_frontend_has_networks(self):
        nets = self.compose["services"]["frontend"].get("networks", [])
        assert len(nets) > 0

    def test_frontend_has_port(self):
        ports = self.compose["services"]["frontend"].get("ports", [])
        assert len(ports) > 0

    def test_frontend_no_volumes(self):
        vols = self.compose["services"]["frontend"].get("volumes", [])
        assert len(vols) == 0


# ─── Script standards ─────────────────────────────────────────────


class TestFrontendDeployStandards:

    @pytest.mark.parametrize("script", [
        "deploy-frontend.sh",
        "build-frontend.sh",
    ])
    def test_has_shebang(self, script):
        content = read_script(script)
        assert content.startswith("#!/bin/bash")

    @pytest.mark.parametrize("script", [
        "deploy-frontend.sh",
        "build-frontend.sh",
    ])
    def test_set_e(self, script):
        content = read_script(script)
        assert "set -e" in content

    @pytest.mark.parametrize("script", [
        "deploy-frontend.sh",
        "build-frontend.sh",
    ])
    def test_uses_npm(self, script):
        content = read_script(script)
        assert "npm" in content
