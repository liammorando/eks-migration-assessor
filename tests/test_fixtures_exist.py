from pathlib import Path

FIXTURES_ROOT = Path(__file__).parent.parent / "fixtures"


def test_ready_app_exists():
    ready_app = FIXTURES_ROOT / "ready-app"
    assert ready_app.is_dir(), "fixtures/ready-app directory missing"
    assert (ready_app / "app.py").is_file(), "ready-app/app.py missing"
    assert (ready_app / "requirements.txt").is_file(), "ready-app/requirements.txt missing"
    assert (ready_app / "Dockerfile").is_file(), "ready-app/Dockerfile missing"
    assert (ready_app / ".dockerignore").is_file(), "ready-app/.dockerignore missing"


def test_stateful_app_exists():
    stateful_app = FIXTURES_ROOT / "stateful-app"
    assert stateful_app.is_dir(), "fixtures/stateful-app directory missing"
    assert (stateful_app / "app.py").is_file(), "stateful-app/app.py missing"
    assert (stateful_app / "requirements.txt").is_file(), "stateful-app/requirements.txt missing"
    assert (stateful_app / "Dockerfile").is_file(), "stateful-app/Dockerfile missing"


def test_messy_compose_exists():
    messy_compose = FIXTURES_ROOT / "messy-compose"
    assert messy_compose.is_dir(), "fixtures/messy-compose directory missing"
    assert (messy_compose / "docker-compose.yml").is_file()
    assert (messy_compose / "app.db").is_file()


def test_fixtures_readme_exists():
    assert (FIXTURES_ROOT / "README.md").is_file()
