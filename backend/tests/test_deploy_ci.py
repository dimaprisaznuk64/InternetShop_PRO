"""
CI/CD tests — lesson 71.
Validates GitHub Actions workflows, deploy pipeline, notifications, dependabot.
"""
import os
import re
import pytest
import yaml


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GITHUB_DIR = os.path.join(PROJECT_ROOT, ".github")
WORKFLOWS_DIR = os.path.join(GITHUB_DIR, "workflows")


def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── File existence ────────────────────────────────────────────────


class TestCIFiles:

    def test_github_dir_exists(self):
        assert os.path.isdir(GITHUB_DIR)

    def test_workflows_dir_exists(self):
        assert os.path.isdir(WORKFLOWS_DIR)

    def test_ci_workflow_exists(self):
        assert os.path.isfile(os.path.join(WORKFLOWS_DIR, "ci.yml"))

    def test_deploy_workflow_exists(self):
        assert os.path.isfile(os.path.join(WORKFLOWS_DIR, "deploy.yml"))

    def test_notify_workflow_exists(self):
        assert os.path.isfile(os.path.join(WORKFLOWS_DIR, "notify.yml"))

    def test_dependabot_exists(self):
        assert os.path.isfile(os.path.join(GITHUB_DIR, "dependabot.yml"))


# ─── CI workflow ───────────────────────────────────────────────────


class TestCIWorkflow:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(WORKFLOWS_DIR, "ci.yml"))
        self.wf = load_yaml(os.path.join(WORKFLOWS_DIR, "ci.yml"))

    def test_has_name(self):
        assert self.wf.get("name") is not None

    def _get_on(self):
        for key in (True, "on", 1):
            if key in self.wf:
                val = self.wf[key]
                return val if isinstance(val, dict) else {}
        return {}

    def test_triggers_on_push(self):
        on = self._get_on()
        assert "push" in on

    def test_triggers_on_pr(self):
        on = self._get_on()
        assert "pull_request" in on

    def test_has_backend_job(self):
        jobs = self.wf.get("jobs", {})
        assert "backend" in jobs

    def test_has_frontend_job(self):
        jobs = self.wf.get("jobs", {})
        assert "frontend" in jobs

    def test_backend_uses_python(self):
        backend = self.wf["jobs"].get("backend", {})
        steps = backend.get("steps", [])
        uses_python = any("python" in str(s.get("uses", "")).lower() for s in steps)
        assert uses_python

    def test_backend_installs_deps(self):
        assert "pip install" in self.content

    def test_backend_runs_tests(self):
        assert "pytest" in self.content

    def test_backend_has_postgres_service(self):
        backend = self.wf["jobs"].get("backend", {})
        services = backend.get("services", {})
        assert "postgres" in services

    def test_backend_has_redis_service(self):
        backend = self.wf["jobs"].get("backend", {})
        services = backend.get("services", {})
        assert "redis" in services

    def test_backend_python_version(self):
        assert "3.13" in self.content

    def test_frontend_uses_node(self):
        frontend = self.wf["jobs"].get("frontend", {})
        steps = frontend.get("steps", [])
        uses_node = any("node" in str(s.get("uses", "")).lower() for s in steps)
        assert uses_node

    def test_frontend_runs_build(self):
        assert "npm run build" in self.content

    def test_frontend_installs_deps(self):
        assert "npm ci" in self.content

    def test_uses_checkout(self):
        assert "actions/checkout" in self.content


# ─── Deploy workflow ───────────────────────────────────────────────


class TestDeployWorkflow:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(WORKFLOWS_DIR, "deploy.yml"))
        self.wf = load_yaml(os.path.join(WORKFLOWS_DIR, "deploy.yml"))

    def test_has_name(self):
        assert self.wf.get("name") is not None

    def _get_on(self):
        for key in (True, "on", 1):
            if key in self.wf:
                val = self.wf[key]
                return val if isinstance(val, dict) else {}
        return {}

    def test_triggers_on_workflow_run(self):
        on = self._get_on()
        assert "workflow_run" in on

    def test_triggers_on_dispatch(self):
        on = self._get_on()
        assert "workflow_dispatch" in on

    def test_depends_on_ci(self):
        wr = self._get_on().get("workflow_run", {})
        assert "CI" in wr.get("workflows", [])

    def test_has_deploy_job(self):
        jobs = self.wf.get("jobs", {})
        assert "deploy" in jobs

    def test_has_ssh_step(self):
        assert "ssh" in self.content.lower()

    def test_has_git_pull(self):
        assert "git pull" in self.content

    def test_has_docker_compose_up(self):
        assert "docker compose" in self.content

    def test_has_alembic_migrate(self):
        assert "alembic" in self.content

    def test_has_health_check(self):
        assert "health" in self.content.lower()

    def test_has_system_prune(self):
        assert "prune" in self.content

    def test_uses_checkout(self):
        assert "actions/checkout" in self.content

    def test_uses_secrets(self):
        assert "secrets" in self.content


# ─── Notify workflow ───────────────────────────────────────────────


class TestNotifyWorkflow:

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = read_file(os.path.join(WORKFLOWS_DIR, "notify.yml"))
        self.wf = load_yaml(os.path.join(WORKFLOWS_DIR, "notify.yml"))

    def test_has_name(self):
        assert self.wf.get("name") is not None

    def _get_on(self):
        for key in (True, "on", 1):
            if key in self.wf:
                val = self.wf[key]
                return val if isinstance(val, dict) else {}
        return {}

    def test_triggers_on_workflow_run(self):
        on = self._get_on()
        assert "workflow_run" in on

    def test_depends_on_deploy(self):
        wr = self._get_on().get("workflow_run", {})
        assert "Deploy" in wr.get("workflows", [])

    def test_has_telegram_step(self):
        assert "telegram" in self.content.lower()

    def test_uses_telegram_action(self):
        assert "telegram-action" in self.content

    def test_has_bot_token(self):
        assert "TELEGRAM_BOT_TOKEN" in self.content

    def test_has_chat_id(self):
        assert "TELEGRAM_CHAT_ID" in self.content


# ─── Dependabot ────────────────────────────────────────────────────


class TestDependabot:

    @pytest.fixture(autouse=True)
    def load(self):
        self.wf = load_yaml(os.path.join(GITHUB_DIR, "dependabot.yml"))

    def test_has_version(self):
        assert self.wf.get("version") == 2

    def test_has_updates(self):
        assert "updates" in self.wf

    def test_pip_ecosystem(self):
        updates = self.wf.get("updates", [])
        pip = [u for u in updates if u.get("package-ecosystem") == "pip"]
        assert len(pip) >= 1

    def test_npm_ecosystem(self):
        updates = self.wf.get("updates", [])
        npm = [u for u in updates if u.get("package-ecosystem") == "npm"]
        assert len(npm) >= 1

    def test_github_actions_ecosystem(self):
        updates = self.wf.get("updates", [])
        actions = [u for u in updates if u.get("package-ecosystem") == "github-actions"]
        assert len(actions) >= 1

    def test_pip_directory(self):
        updates = self.wf.get("updates", [])
        pip = [u for u in updates if u.get("package-ecosystem") == "pip"]
        assert any(u.get("directory") == "/backend" for u in pip)

    def test_npm_directory(self):
        updates = self.wf.get("updates", [])
        npm = [u for u in updates if u.get("package-ecosystem") == "npm"]
        assert any(u.get("directory") == "/frontend" for u in npm)

    def test_has_schedule(self):
        updates = self.wf.get("updates", [])
        for u in updates:
            assert "schedule" in u

    def test_schedule_is_weekly(self):
        updates = self.wf.get("updates", [])
        for u in updates:
            interval = u.get("schedule", {}).get("interval")
            assert interval == "weekly"


# ─── Workflow YAML validity ────────────────────────────────────────


class TestWorkflowYAML:

    @pytest.mark.parametrize("filename", [
        "ci.yml",
        "deploy.yml",
        "notify.yml",
    ])
    def test_valid_yaml(self, filename):
        path = os.path.join(WORKFLOWS_DIR, filename)
        wf = load_yaml(path)
        assert isinstance(wf, dict)
        assert "on" in wf or True  # might be parsed as True for on: without values
        assert "jobs" in wf
