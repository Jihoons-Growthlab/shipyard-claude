import shutil
import time

import pytest
from fastapi.testclient import TestClient

from app import config
from app.db import connect, migrate
from app.seed import DEMO_TOTP_SECRET, seed_hulls, seed_plans, seed_system
from app.security import totp_at
from app.services import auth_service


@pytest.fixture(scope="session")
def template_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("tpl") / "template.db"
    conn = connect(str(path))
    migrate(conn)
    seed_system(conn)
    seed_hulls(conn)
    conn.close()
    return path


@pytest.fixture(scope="session")
def full_template_db(template_db, tmp_path_factory):
    """System + hulls + F05 plan/drawing seed (P1/P2 tests keep the lighter template)."""
    path = tmp_path_factory.mktemp("tplfull") / "full.db"
    shutil.copy(template_db, path)
    conn = connect(str(path))
    seed_plans(conn)
    conn.close()
    return path


@pytest.fixture
def db_path(request, template_db, tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    full = request.node.get_closest_marker("full_seed") is not None
    shutil.copy(request.getfixturevalue("full_template_db") if full else template_db, path)
    monkeypatch.setattr(config.settings, "db_path", str(path))
    monkeypatch.setattr(config.settings, "file_dir", str(tmp_path / "files"))  # D12: isolated PDF storage
    auth_service._otp_fails.clear()
    auth_service._otp_used.clear()
    return path


@pytest.fixture
def client(db_path):
    from app.main import create_app
    return TestClient(create_app())


@pytest.fixture
def db(db_path):
    conn = connect(str(db_path))
    yield conn
    conn.close()


def current_otp(secret=DEMO_TOTP_SECRET):
    return totp_at(secret, int(time.time() // 30))


def login(client, emp, pw):
    r = client.post("/api/auth/login", json={"emp_no": emp, "password": pw})
    assert r.status_code == 200, r.text
    body = r.json()
    if body["otp_required"]:
        r = client.post("/api/auth/otp/verify", json={"code": current_otp()},
                        headers={"Authorization": f"Bearer {body['otp_token']}"})
        assert r.status_code == 200, r.text
        body = r.json()
    return {"Authorization": f"Bearer {body['access_token']}"}
