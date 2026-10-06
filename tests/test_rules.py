from __future__ import annotations

import tempfile
from pathlib import Path

from assessor.models import Severity
from assessor.repo import iter_files
from assessor.scanner.registry import ScanContext, run_all
from assessor.scanner.rules import *  # registers all rules


def _create_ctx(tmp_path: Path, files: dict[str, str]) -> ScanContext:
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    all_files = list(iter_files(tmp_path))
    return ScanContext(root=tmp_path, files=all_files)


class TestStateRules:
    def test_state_001_local_writes_detected(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'open("/var/data/uploads", "w").write("x")\n',
        })
        findings = run_all(ctx)
        assert any(f.id == "STATE-001" for f in findings)

    def test_state_001_no_false_positive_on_read(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'open("/var/data/uploads", "r").read()\n',
        })
        findings = run_all(ctx)
        assert not any(f.id == "STATE-001" for f in findings)

    def test_state_002_in_memory_sessions(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "SESSIONS = {}\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "STATE-002" for f in findings)

    def test_state_002_no_false_positive_on_external_store(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import redis\nr = redis.Redis()\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "STATE-002" for f in findings)

    def test_state_003_sqlite_detected(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import sqlite3\nconn = sqlite3.connect('app.db')\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "STATE-003" for f in findings)

    def test_state_003_no_false_positive_on_postgres(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import psycopg2\nconn = psycopg2.connect('postgresql://...')\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "STATE-003" for f in findings)


class TestConfigRules:
    def test_cfg_001_hardcoded_secret(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'SECRET_KEY = "supersecret123"\n',
        })
        findings = run_all(ctx)
        assert any(f.id == "CFG-001" for f in findings)

    def test_cfg_001_aws_key(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'AWS_KEY = "AKIAFAKEFAKEFAKEFAKE"\n',
        })
        findings = run_all(ctx)
        assert any(f.id == "CFG-001" for f in findings)

    def test_cfg_001_no_false_positive_on_env(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'SECRET_KEY = os.getenv("SECRET_KEY")\n',
        })
        findings = run_all(ctx)
        assert not any(f.id == "CFG-001" for f in findings)

    def test_cfg_002_no_env_config(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "DEBUG = True\nPORT = 8080\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CFG-002" for f in findings)

    def test_cfg_002_has_env_config(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import os\nDEBUG = os.getenv('DEBUG', 'false')\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "CFG-002" for f in findings)


class TestNetworkRules:
    def test_net_001_localhost(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'DB_HOST = "localhost"\n',
        })
        findings = run_all(ctx)
        assert any(f.id == "NET-001" for f in findings)

    def test_net_001_private_ip(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'API_URL = "http://192.168.1.50:8080"\n',
        })
        findings = run_all(ctx)
        assert any(f.id == "NET-001" for f in findings)

    def test_net_001_no_false_positive_on_service_name(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'DB_HOST = "postgres.default.svc.cluster.local"\n',
        })
        findings = run_all(ctx)
        assert not any(f.id == "NET-001" for f in findings)

    def test_net_002_hardcoded_port(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "PORT = 8080\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "NET-002" for f in findings)

    def test_net_002_no_false_positive_on_env_port(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import os\nPORT = int(os.getenv('PORT', '8080'))\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "NET-002" for f in findings)


class TestContainerRules:
    def test_ctr_001_no_dockerfile(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "print('hello')\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CTR-001" for f in findings)

    def test_ctr_001_has_dockerfile(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\n",
            "app.py": "print('hello')\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "CTR-001" for f in findings)

    def test_ctr_002_no_user(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\nRUN pip install flask\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CTR-002" for f in findings)

    def test_ctr_002_has_user(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\nUSER appuser\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "CTR-002" for f in findings)

    def test_ctr_003_latest_tag(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:latest\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CTR-003" for f in findings)

    def test_ctr_003_no_tag(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CTR-003" for f in findings)

    def test_ctr_003_pinned_tag(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "CTR-003" for f in findings)

    def test_ctr_004_no_healthcheck_no_endpoint(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\n",
            "app.py": "print('hello')\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CTR-004" for f in findings)

    def test_ctr_004_has_healthcheck(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\nHEALTHCHECK CMD curl -f http://localhost/healthz\n",
            "app.py": "print('hello')\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "CTR-004" for f in findings)

    def test_ctr_004_has_health_endpoint(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\n",
            "app.py": "@app.route('/healthz')\ndef healthz():\n    return 'ok'\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "CTR-004" for f in findings)


class TestLoggingRules:
    def test_log_001_file_handler(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import logging\nlogging.FileHandler('/var/log/app.log')\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "LOG-001" for f in findings)

    def test_log_001_no_false_positive_on_stdout(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import logging\nlogging.basicConfig(level=logging.INFO)\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "LOG-001" for f in findings)


class TestLifecycleRules:
    def test_life_001_no_sigterm(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "print('hello')\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "LIFE-001" for f in findings)

    def test_life_001_has_sigterm(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import signal\nsignal.signal(signal.SIGTERM, handler)\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "LIFE-001" for f in findings)


class TestComposeRules:
    def test_cmp_001_host_bind(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "docker-compose.yml": "services:\n  web:\n    volumes:\n      - /home/user/data:/data\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CMP-001" for f in findings)

    def test_cmp_002_privileged(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "docker-compose.yml": "services:\n  web:\n    privileged: true\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CMP-002" for f in findings)

    def test_cmp_002_host_network(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "docker-compose.yml": "services:\n  web:\n    network_mode: host\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CMP-002" for f in findings)

    def test_cmp_003_container_name(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "docker-compose.yml": "services:\n  web:\n    container_name: my-web\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CMP-003" for f in findings)

    def test_cmp_003_depends_on(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "docker-compose.yml": "services:\n  web:\n    depends_on:\n      db:\n        condition: service_healthy\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CMP-003" for f in findings)

    def test_cmp_004_missing_dockerfile(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "docker-compose.yml": "services:\n  web:\n    build: .\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "CMP-004" for f in findings)

    def test_cmp_004_has_dockerfile(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "docker-compose.yml": "services:\n  web:\n    build: .\n",
            "Dockerfile": "FROM python:3.12-slim\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "CMP-004" for f in findings)


class TestPositiveRules:
    def test_ok_001_stdout_logging(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import logging\nlogging.basicConfig(level=logging.INFO)\n",
        })
        findings = run_all(ctx)
        ok_findings = [f for f in findings if f.id == "OK-001" and "stdout" in f.title]
        assert len(ok_findings) >= 1

    def test_ok_001_env_config(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "import os\nPORT = os.getenv('PORT', '8080')\n",
        })
        findings = run_all(ctx)
        ok_findings = [f for f in findings if f.id == "OK-001" and "environment" in f.title]
        assert len(ok_findings) >= 1

    def test_ok_001_health_endpoint(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "@app.route('/healthz')\ndef healthz():\n    return 'ok'\n",
        })
        findings = run_all(ctx)
        ok_findings = [f for f in findings if f.id == "OK-001" and "health" in f.title.lower()]
        assert len(ok_findings) >= 1

    def test_ok_001_non_root_user(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\nUSER appuser\n",
        })
        findings = run_all(ctx)
        ok_findings = [f for f in findings if f.id == "OK-001" and "non-root" in f.title.lower()]
        assert len(ok_findings) >= 1

    def test_ok_001_healthcheck(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\nHEALTHCHECK CMD curl -f http://localhost/healthz\n",
        })
        findings = run_all(ctx)
        ok_findings = [f for f in findings if f.id == "OK-001" and "HEALTHCHECK" in f.title]
        assert len(ok_findings) >= 1

    def test_ok_001_pinned_tag(self):
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "Dockerfile": "FROM python:3.12-slim\n",
        })
        findings = run_all(ctx)
        ok_findings = [f for f in findings if f.id == "OK-001" and "pinned" in f.title.lower()]
        assert len(ok_findings) >= 1


class TestDocumentationHandling:
    def test_state_003_skipped_in_readme(self):
        """README.md with CREATE TABLE should not trigger STATE-003."""
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "README.md": "# Database Schema\n\n```sql\nCREATE TABLE users (\n    id INT PRIMARY KEY\n);\n```\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "STATE-003" for f in findings)

    def test_state_003_still_detected_in_py(self):
        """CREATE TABLE in .py file should still trigger STATE-003."""
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": "sql = \"\"\"CREATE TABLE users (id INT PRIMARY KEY);\"\"\"\n",
        })
        findings = run_all(ctx)
        assert any(f.id == "STATE-003" for f in findings)

    def test_net_001_skipped_in_readme(self):
        """README.md with localhost:8080 should not trigger NET-001."""
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "README.md": "# Local Development\n\nRun the server:\n\n```\nlocalhost:8080\n```\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "NET-001" for f in findings)

    def test_net_001_still_detected_in_py(self):
        """localhost:8080 in .py file should still trigger NET-001."""
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'DB_HOST = "localhost:8080"\n',
        })
        findings = run_all(ctx)
        assert any(f.id == "NET-001" for f in findings)

    def test_cfg_001_downgraded_in_docs(self):
        """Secret in documentation file should have downgraded severity (HIGH instead of CRITICAL)."""
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "docs/architecture.md": 'API_KEY = "supersecret123"\n',
        })
        findings = run_all(ctx)
        cfg_findings = [f for f in findings if f.id == "CFG-001"]
        assert len(cfg_findings) == 1
        assert cfg_findings[0].severity == Severity.HIGH  # Downgraded from CRITICAL

    def test_cfg_001_critical_in_code(self):
        """Secret in code file should have CRITICAL severity."""
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "app.py": 'API_KEY = "supersecret123"\n',
        })
        findings = run_all(ctx)
        cfg_findings = [f for f in findings if f.id == "CFG-001"]
        assert len(cfg_findings) == 1
        assert cfg_findings[0].severity == Severity.CRITICAL

    def test_state_001_skipped_in_docs_dir(self):
        """State rules should be skipped in docs/ directory."""
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "docs/guide.md": 'open("/var/data/file.txt", "w")\n',
        })
        findings = run_all(ctx)
        assert not any(f.id == "STATE-001" for f in findings)

    def test_log_001_skipped_in_examples(self):
        """LOG-001 should be skipped in examples/ directory."""
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "examples/logging.py": "logging.FileHandler('/var/log/app.log')\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "LOG-001" for f in findings)

    def test_life_001_skipped_in_changelog(self):
        """LIFE-001 should be skipped in CHANGELOG files."""
        ctx = _create_ctx(Path(tempfile.mkdtemp()), {
            "CHANGELOG.md": "## 1.0.0\n- Added signal.signal(SIGTERM, handler)\n",
        })
        findings = run_all(ctx)
        assert not any(f.id == "LIFE-001" for f in findings)


class TestFixtures:
    def test_ready_app_no_critical_high(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "ready-app"
        files = list(iter_files(fixture))
        ctx = ScanContext(root=fixture, files=files)
        findings = run_all(ctx)
        critical_high = [f for f in findings if f.severity in (Severity.CRITICAL, Severity.HIGH)]
        # Print findings for debugging
        for f in critical_high:
            print(f"CRITICAL/HIGH: {f.id} - {f.title} in {f.file}:{f.line}")
        assert len(critical_high) == 0, f"ready-app has {len(critical_high)} critical/high findings: {[f.id for f in critical_high]}"

    def test_stateful_app_has_expected_findings(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "stateful-app"
        files = list(iter_files(fixture))
        ctx = ScanContext(root=fixture, files=files)
        findings = run_all(ctx)
        finding_ids = {f.id for f in findings}
        # stateful-app has /healthz endpoint, so CTR-004 should NOT fire
        expected = {"STATE-001", "STATE-002", "NET-001", "CFG-001", "LOG-001", "CTR-002", "CTR-003"}
        for e in expected:
            assert e in finding_ids, f"stateful-app missing {e}; found: {finding_ids}"

    def test_messy_compose_has_expected_findings(self):
        fixture = Path(__file__).parent.parent / "fixtures" / "messy-compose"
        files = list(iter_files(fixture))
        ctx = ScanContext(root=fixture, files=files)
        findings = run_all(ctx)
        finding_ids = {f.id for f in findings}
        expected = {"CMP-001", "CMP-002", "STATE-003", "CMP-004"}
        for e in expected:
            assert e in finding_ids, f"messy-compose missing {e}; found: {finding_ids}"
