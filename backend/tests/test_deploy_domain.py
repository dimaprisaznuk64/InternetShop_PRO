"""
Domain + HTTPS tests — lesson 68.
Validates SSL setup, DNS configuration, certbot automation, HTTPS enforcement.
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


class TestSSLFilesExist:

    def test_ssl_setup_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "ssl-setup.sh"))

    def test_dns_check_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "dns-check.sh"))

    def test_nginx_prod_config_exists(self):
        assert os.path.isfile(os.path.join(DEPLOY_DIR, "nginx", "internetshop.conf"))


# ─── SSL setup script ─────────────────────────────────────────────


class TestSSLSetup:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("ssl-setup.sh")

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_installs_certbot(self):
        assert "certbot" in self.content

    def test_installs_nginx_plugin(self):
        assert "certbot-nginx" in self.content or "python3-certbot-nginx" in self.content

    def test_uses_webroot(self):
        assert "--webroot" in self.content

    def test_agree_tos(self):
        assert "--agree-tos" in self.content

    def test_no_eff_email(self):
        assert "--no-eff-email" in self.content

    def test_creates_ssl_server_block(self):
        assert "listen 443" in self.content

    def test_ssl_certificate_path(self):
        assert "letsencrypt" in self.content.lower()

    def test_ssl_protocols(self):
        assert "TLSv1.2" in self.content and "TLSv1.3" in self.content

    def test_http_redirect(self):
        assert "301" in self.content and "https" in self.content

    def test_tests_nginx_config(self):
        assert "nginx -t" in self.content

    def test_reloads_nginx(self):
        assert "systemctl reload nginx" in self.content

    def test_accepts_domain_argument(self):
        assert "${1:" in self.content or "$1" in self.content

    def test_accepts_email_argument(self):
        assert "${2:" in self.content or "$2" in self.content

    def test_removes_default_site(self):
        assert "default" in self.content and "rm" in self.content

    def test_enables_site(self):
        assert "sites-enabled" in self.content

    def test_hsts_header(self):
        assert "Strict-Transport-Security" in self.content

    def test_security_headers(self):
        assert "X-Frame-Options" in self.content
        assert "X-Content-Type-Options" in self.content


# ─── DNS check script ─────────────────────────────────────────────


class TestDNSCheck:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_script("dns-check.sh")

    def test_has_shebang(self):
        assert self.content.startswith("#!/bin/bash")

    def test_set_euo_pipefail(self):
        assert "set -euo pipefail" in self.content

    def test_uses_dig(self):
        assert "dig" in self.content

    def test_checks_a_record(self):
        assert "A" in self.content and "record" in self.content.lower()

    def test_checks_www(self):
        assert "www" in self.content

    def test_checks_multiple_nameservers(self):
        assert "8.8.8.8" in self.content
        assert "1.1.1.1" in self.content

    def test_accepts_domain_argument(self):
        assert "${1:" in self.content or "$1" in self.content

    def test_accepts_server_ip(self):
        assert "${2:" in self.content or "$2" in self.content

    def test_counts_failures(self):
        assert "FAILURES" in self.content

    def test_compares_ip(self):
        assert "SERVER_IP" in self.content


# ─── Nginx production config SSL params ───────────────────────────


class TestNginxSSLParams:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "nginx", "internetshop.conf"))

    def test_listens_443_ssl(self):
        assert "listen 443 ssl" in self.content

    def test_ssl_protocols_strict(self):
        assert "TLSv1.2" in self.content
        assert "TLSv1.3" in self.content
        assert "TLSv1" in self.content and "TLSv1.0" not in self.content
        assert "SSLv3" not in self.content

    def test_ssl_ciphers_strong(self):
        assert "HIGH:!aNULL:!MD5" in self.content

    def test_ssl_prefer_server_ciphers(self):
        assert "ssl_prefer_server_ciphers on" in self.content

    def test_ssl_session_cache(self):
        assert "ssl_session_cache" in self.content

    def test_ssl_session_timeout(self):
        assert "ssl_session_timeout" in self.content

    def test_hsts_max_age(self):
        hsts_match = re.search(r"max-age=(\d+)", self.content)
        assert hsts_match is not None
        assert int(hsts_match.group(1)) >= 31536000

    def test_hsts_include_subdomains(self):
        assert "includeSubDomains" in self.content

    def test_letsencrypt_cert_path(self):
        assert "letsencrypt" in self.content.lower()
        assert "fullchain.pem" in self.content
        assert "privkey.pem" in self.content

    def test_http_to_https_redirect(self):
        lines = self.content.splitlines()
        in_server_80 = False
        for line in lines:
            if "listen 80" in line:
                in_server_80 = True
            if in_server_80 and "301" in line and "https" in line:
                return
        pytest.fail("No HTTP→HTTPS redirect found in port 80 server block")


# ─── HTTPS enforcement checks ─────────────────────────────────────


class TestHTTPSEnforcement:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(DEPLOY_DIR, "nginx", "internetshop.conf"))

    def test_two_server_blocks(self):
        server_count = self.content.count("server {")
        assert server_count >= 2, "Need separate server blocks for HTTP redirect and HTTPS"

    def test_no_plaintext_api(self):
        for line in self.content.splitlines():
            stripped = line.strip()
            if "proxy_pass" in stripped and "http://" in stripped:
                assert "https://" not in stripped or "127.0.0.1" in stripped

    def test_security_headers_in_ssl_block(self):
        ssl_section = self.content[self.content.find("listen 443"):]
        assert "X-Frame-Options" in ssl_section
        assert "X-Content-Type-Options" in ssl_section


# ─── Script standards ─────────────────────────────────────────────


class TestDomainScriptStandards:

    @pytest.mark.parametrize("script", [
        "ssl-setup.sh",
        "dns-check.sh",
    ])
    def test_has_shebang(self, script):
        content = read_script(script)
        assert content.startswith("#!/bin/bash")

    @pytest.mark.parametrize("script", [
        "ssl-setup.sh",
        "dns-check.sh",
    ])
    def test_set_e(self, script):
        content = read_script(script)
        assert "set -e" in content

    @pytest.mark.parametrize("script", [
        "ssl-setup.sh",
        "dns-check.sh",
    ])
    def test_accepts_arguments(self, script):
        content = read_script(script)
        assert "Usage" in content or "${1:" in content or "$1" in content
