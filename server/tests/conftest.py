import os
import sys
import tempfile

import pytest

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["ENABLE_WORKER"] = "false"
os.environ["FIREBASE_CREDENTIALS"] = ""
os.environ["SMS_PROVIDER"] = "console"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db():
    s = SessionLocal()
    yield s
    s.close()


def register(client, email="nguoinha@example.com", phone="+84900000001", name="Người nhà"):
    r = client.post("/api/auth/register", json={"email": email, "password": "matkhau123",
                                                "full_name": name, "phone": phone})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def setup(client):
    """Tài khoản người nhà + 1 bệnh nhân + 1 thiết bị. Trả về (headers, patient_id, device_headers)."""
    h = register(client)
    pid = client.post("/api/patients", json={"full_name": "Bà Nguyễn Thị A", "birth_year": 1945},
                      headers=h).json()["id"]
    dev = client.post(f"/api/patients/{pid}/devices", json={"name": "Đồng hồ 1"}, headers=h).json()
    return h, pid, {"X-Device-Key": dev["api_key"]}
