"""
Docker configuration tests — lesson 61.
Validates Dockerfiles, .dockerignore, nginx config, multi-stage builds.
"""
import os
import re
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─── Backend Dockerfile ────────────────────────────────────────────


class TestBackendDockerfileExists:

    def test_dockerfile_exists(self):
        assert os.path.isfile(os.path.join(BACKEND_DIR, "Dockerfile"))


class TestBackendDockerfileBase:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(BACKEND_DIR, "Dockerfile"))

    def test_from_python_base_image(self):
        assert re.search(r"^FROM\s+python:", self.content, re.MULTILINE)

    def test_python_slim_image(self):
        assert "python:" in self.content and "slim" in self.content

    def test_workdir_set(self):
        assert "WORKDIR" in self.content

    def test_exposes_port_8000(self):
        assert "EXPOSE 8000" in self.content


class TestBackendDockerfileSecurity:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(BACKEND_DIR, "Dockerfile"))

    def test_non_root_user_created(self):
        assert re.search(r"adduser.*--system", self.content) or re.search(
            r"useradd", self.content
        )

    def test_user_switched_with_user_directive(self):
        assert re.search(r"^USER\s+\w+", self.content, re.MULTILINE)


class TestBackendDockerfileDependencies:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(BACKEND_DIR, "Dockerfile"))

    def test_copies_requirements_first(self):
        req_pos = self.content.find("requirements.txt")
        app_pos = self.content.find("COPY . .")
        assert req_pos < app_pos, "requirements.txt must be copied before source"

    def test_pip_install_no_cache(self):
        assert "pip install" in self.content and "--no-cache-dir" in self.content

    def test_pip_installs_from_requirements(self):
        assert "pip install" in self.content and "requirements.txt" in self.content


class TestBackendDockerfileCMD:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(BACKEND_DIR, "Dockerfile"))

    def test_cmd_uses_uvicorn(self):
        assert "uvicorn" in self.content

    def test_cmd_binds_to_0_0_0_0(self):
        assert "0.0.0.0" in self.content

    def test_cmd_port_8000(self):
        assert "8000" in self.content


# ─── Frontend Dockerfile ───────────────────────────────────────────


class TestFrontendDockerfileExists:

    def test_dockerfile_exists(self):
        assert os.path.isfile(os.path.join(FRONTEND_DIR, "Dockerfile"))


class TestFrontendDockerfileMultiStage:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(FRONTEND_DIR, "Dockerfile"))

    def test_multi_stage_build(self):
        from_count = len(re.findall(r"^FROM\s+", self.content, re.MULTILINE))
        assert from_count >= 2, "Must have at least 2 FROM for multi-stage build"

    def test_build_stage_uses_node(self):
        lines = [
            l for l in self.content.splitlines() if l.strip().upper().startswith("FROM")
        ]
        assert any("node" in l.lower() for l in lines)

    def test_serve_stage_uses_nginx(self):
        lines = [
            l for l in self.content.splitlines() if l.strip().upper().startswith("FROM")
        ]
        assert any("nginx" in l.lower() for l in lines)


class TestFrontendDockerfileBuild:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(FRONTEND_DIR, "Dockerfile"))

    def test_npm_ci_installs_deps(self):
        assert "npm ci" in self.content

    def test_copies_package_json_first(self):
        pkg_pos = self.content.find("package.json")
        build_pos = self.content.find("npm run build")
        assert pkg_pos < build_pos

    def test_copies_build_output(self):
        assert "dist" in self.content


class TestFrontendDockerfileServe:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(FRONTEND_DIR, "Dockerfile"))

    def test_nginx_serves_from_html(self):
        assert "/usr/share/nginx/html" in self.content

    def test_nginx_config_copied(self):
        assert "nginx.conf" in self.content

    def test_exposes_port_80(self):
        assert "EXPOSE 80" in self.content


# ─── Nginx configuration ──────────────────────────────────────────


class TestNginxConfigExists:

    def test_nginx_conf_exists(self):
        assert os.path.isfile(os.path.join(FRONTEND_DIR, "nginx.conf"))


class TestNginxSPAConfig:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(FRONTEND_DIR, "nginx.conf"))

    def test_listen_port_80(self):
        assert "listen 80" in self.content

    def test_try_files_fallback(self):
        assert "try_files" in self.content and "index.html" in self.content

    def test_gzip_enabled(self):
        assert "gzip on" in self.content

    def test_proxy_to_backend(self):
        assert "proxy_pass" in self.content and "backend" in self.content

    def test_caches_static_assets(self):
        assert "expires" in self.content


# ─── .dockerignore ─────────────────────────────────────────────────


class TestBackendDockerignore:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(BACKEND_DIR, ".dockerignore"))

    def test_excludes_venv(self):
        assert ".venv" in self.content

    def test_excludes_pycache(self):
        assert "__pycache__" in self.content

    def test_excludes_env(self):
        assert ".env" in self.content

    def test_excludes_git(self):
        assert ".git" in self.content

    def test_excludes_test_cache(self):
        assert "pytest_cache" in self.content

    def test_preserves_env_example(self):
        assert "!.env.example" in self.content


class TestFrontendDockerignore:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(FRONTEND_DIR, ".dockerignore"))

    def test_excludes_node_modules(self):
        assert "node_modules" in self.content

    def test_excludes_dist(self):
        assert "dist" in self.content

    def test_excludes_env(self):
        assert ".env" in self.content


# ─── Integration: Dockerfile correctness ───────────────────────────


class TestDockerfileSyntax:

    def test_backend_has_no_tabs(self):
        content = read_file(os.path.join(BACKEND_DIR, "Dockerfile"))
        for i, line in enumerate(content.splitlines(), 1):
            assert "\t" not in line, f"Line {i} contains tabs"

    def test_frontend_has_no_tabs(self):
        content = read_file(os.path.join(FRONTEND_DIR, "Dockerfile"))
        for i, line in enumerate(content.splitlines(), 1):
            assert "\t" not in line, f"Line {i} contains tabs"

    def test_nginx_conf_has_no_tabs(self):
        content = read_file(os.path.join(FRONTEND_DIR, "nginx.conf"))
        for i, line in enumerate(content.splitlines(), 1):
            assert "\t" not in line, f"Line {i} contains tabs"


class TestDockerfilePrinciples:

    def test_backend_copies_requirements_before_source(self):
        content = read_file(os.path.join(BACKEND_DIR, "Dockerfile"))
        req_line = None
        copy_all_line = None
        for i, line in enumerate(content.splitlines()):
            stripped = line.strip()
            if "requirements.txt" in stripped and stripped.startswith("COPY"):
                req_line = i
            if stripped == "COPY . .":
                copy_all_line = i
        assert req_line is not None and copy_all_line is not None
        assert req_line < copy_all_line

    def test_frontend_copies_package_json_before_install(self):
        content = read_file(os.path.join(FRONTEND_DIR, "Dockerfile"))
        pkg_line = None
        install_line = None
        for i, line in enumerate(content.splitlines()):
            stripped = line.strip()
            if "package.json" in stripped and stripped.startswith("COPY"):
                pkg_line = i
            if "npm ci" in stripped:
                install_line = i
        assert pkg_line is not None and install_line is not None
        assert pkg_line < install_line

    def test_frontend_build_before_serve_copy(self):
        content = read_file(os.path.join(FRONTEND_DIR, "Dockerfile"))
        build_line = None
        serve_line = None
        for i, line in enumerate(content.splitlines()):
            stripped = line.strip()
            if "npm run build" in stripped:
                build_line = i
            if "COPY --from=build" in stripped:
                serve_line = i
        assert build_line is not None and serve_line is not None
        assert build_line < serve_line
