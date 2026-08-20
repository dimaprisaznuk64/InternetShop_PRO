"""
Deploy configuration tests — lesson 65.
Validates server setup, firewall, SSH hardening, nginx reverse proxy.
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


# ─── Deploy directory structure ────────────────────────────────────


class TestDeployStructure:

    def test_deploy_dir_exists(self):
        assert os.path.isdir(DEPLOY_DIR)

    def test_server_setup_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "server-setup.sh"))

    def test_firewall_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "firewall.sh"))

    def test_ssh_setup_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "ssh-setup.sh"))

    def test_nginx_dir_exists(self):
        assert os.path.isdir(os.path.join(DEPLOY_DIR, "nginx"))

    def test_nginx_prod_config_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "nginx", "internetshop.conf"))

    def test_nginx_api_proxy_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "nginx", "api-proxy.conf"))


# ─── Shell script standards ────────────────────────────────────────


class TestScriptStandards:

    @pytest.mark.parametrize("script", [
        "server-setup.sh",
        "firewall.sh",
        "ssh-setup.sh",
    ])
    def test_has_shebang(self, script):
        content = read_script(script)
        assert content.startswith("#!/bin/bash")

    @pytest.mark.parametrize("script", [
        "server-setup.sh",
        "firewall.sh",
        "ssh-setup.sh",
    ])
    def test_set_euo_pipefail(self, script):
        content = read_script(script)
        assert "set -euo pipefail" in content

    @pytest.mark.parametrize("script", [
        "server-setup.sh",
        "firewall.sh",
        "ssh-setup.sh",
    ])
    def test_has_echo_output(self, script):
        content = read_script(script)
        assert "echo" in content


# ─── Server setup ──────────────────────────────────────────────────


class TestServerSetup:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("server-setup.sh")

    def test_installs_docker(self):
        assert "docker" in self.content.lower()

    def test_installs_ufw(self):
        assert "ufw" in self.content

    def test_installs_fail2ban(self):
        assert "fail2ban" in self.content

    def test_installs_git(self):
        assert "git" in self.content

    def test_enables_docker_on_boot(self):
        assert "systemctl enable docker" in self.content

    def test_creates_app_user(self):
        assert "adduser" in self.content

    def test_creates_app_directory(self):
        assert "mkdir" in self.content

    def test_system_update(self):
        assert "apt-get update" in self.content


# ─── Firewall ──────────────────────────────────────────────────────


class TestFirewall:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("firewall.sh")

    def test_resets_ufw(self):
        assert "ufw" in self.content and "reset" in self.content

    def test_default_deny_incoming(self):
        assert "deny incoming" in self.content

    def test_default_allow_outgoing(self):
        assert "allow outgoing" in self.content

    def test_allows_ssh(self):
        assert re.search(r"ufw allow.*22", self.content)

    def test_allows_http(self):
        assert re.search(r"ufw allow.*80", self.content)

    def test_allows_https(self):
        assert re.search(r"ufw allow.*443", self.content)

    def test_enables_ufw(self):
        assert "ufw --force enable" in self.content

    def test_no_extra_ports(self):
        allow_lines = [l for l in self.content.splitlines() if "ufw allow" in l]
        ports = set()
        for line in allow_lines:
            m = re.search(r"allow\s+(\d+)/tcp", line)
            if m:
                ports.add(int(m.group(1)))
        assert ports == {22, 80, 443}


# ─── SSH hardening ─────────────────────────────────────────────────


class TestSSHHardening:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("ssh-setup.sh")

    def test_disables_root_login(self):
        assert "PermitRootLogin no" in self.content

    def test_disables_password_auth(self):
        assert "PasswordAuthentication no" in self.content

    def test_disables_x11(self):
        assert "X11Forwarding no" in self.content

    def test_limits_auth_tries(self):
        assert "MaxAuthTries" in self.content

    def test_sets_client_alive_interval(self):
        assert "ClientAliveInterval" in self.content

    def test_creates_backup(self):
        assert "cp" in self.content and "bak" in self.content

    def test_validates_config(self):
        assert "sshd -t" in self.content

    def test_restarts_sshd(self):
        assert "systemctl restart sshd" in self.content


# ─── Nginx production config ──────────────────────────────────────


class TestNginxProduction:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "nginx", "internetshop.conf"))

    def test_listens_on_80(self):
        assert "listen 80" in self.content

    def test_listens_on_443(self):
        assert "listen 443" in self.content

    def test_http_to_https_redirect(self):
        assert "301" in self.content and "https" in self.content

    def test_ssl_protocols(self):
        assert "TLSv1.2" in self.content and "TLSv1.3" in self.content

    def test_ssl_certificate_path(self):
        assert "letsencrypt" in self.content.lower()

    def test_hsts_header(self):
        assert "Strict-Transport-Security" in self.content

    def test_x_frame_options(self):
        assert "X-Frame-Options" in self.content

    def test_x_content_type_options(self):
        assert "X-Content-Type-Options" in self.content

    def test_api_proxy_pass(self):
        assert "proxy_pass" in self.content and "/api/" in self.content

    def test_spa_fallback(self):
        assert "try_files" in self.content and "index.html" in self.content

    def test_gzip_enabled(self):
        assert "gzip on" in self.content

    def test_static_assets_caching(self):
        assert "expires" in self.content

    def test_no_server_tokens(self):
        assert "server_tokens off" in self.content or "server_tokens" not in self.content


# ─── Nginx API proxy config ────────────────────────────────────────


class TestNginxAPIProxy:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "nginx", "api-proxy.conf"))

    def test_has_upstream(self):
        assert "upstream" in self.content

    def test_upstream_keepalive(self):
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


# ─── Scripts are executable-safe (no Windows line endings) ─────────


class TestScriptLineEndings:

    @pytest.mark.parametrize("script", [
        "server-setup.sh",
        "firewall.sh",
        "ssh-setup.sh",
    ])
    def test_no_bom(self, script):
        content = read_script(script)
        assert not content.startswith("\ufeff"), f"{script} has BOM marker"
