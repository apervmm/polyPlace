import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.main import app

JWT_SECRET = "test-secret"
USER_ID = "11111111-1111-1111-1111-111111111111"


@pytest.fixture(autouse=True)
def _settings(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused/unused")
    monkeypatch.setenv("PLACE_COOLDOWN_SECONDS", "100")
    yield


@pytest.fixture(autouse=True)
def _no_real_db(monkeypatch):
    # main.py imports these names directly (`from .db import ...`), so the
    # mocks must be installed on `app.main`, not `app.db` - patching the
    # source module wouldn't affect main's already-bound local references.
    monkeypatch.setattr(main, "init_pool", AsyncMock(return_value=AsyncMock()))
    monkeypatch.setattr(main, "get_state", AsyncMock(return_value=[]))

    async def fake_insert_action(pool, x, y, color, user_id):
        return {
            "x": x,
            "y": y,
            "color": color,
            "userid": user_id,
            "timestamp": datetime.now(timezone.utc),
        }

    monkeypatch.setattr(main, "insert_action", AsyncMock(side_effect=fake_insert_action))
    yield


def _token() -> str:
    return jwt.encode({"userId": USER_ID}, JWT_SECRET, algorithm="HS256")


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_guest_connect_gets_init_with_null_user_id(client):
    with client.websocket_connect("/") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "init"
        assert msg["userId"] is None


def test_authed_connect_gets_init_with_matching_user_id(client):
    with client.websocket_connect(f"/?token={_token()}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "init"
        assert msg["userId"] == USER_ID


def test_guest_place_is_rejected_without_db_write(client):
    with client.websocket_connect("/") as ws:
        ws.receive_json()  # init
        ws.send_json({"type": "place", "x": 1, "y": 1, "color": "#ff0000"})
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["code"] == "unauthenticated"
        main.insert_action.assert_not_called()


def test_authed_place_broadcasts_update_then_cooldown_rejects_second(client):
    with client.websocket_connect(f"/?token={_token()}") as ws:
        ws.receive_json()  # init
        ws.send_json({"type": "place", "x": 2, "y": 3, "color": "#0000ff"})
        update = ws.receive_json()
        assert update["type"] == "update"
        assert update["x"] == 2 and update["y"] == 3
        assert update["userId"] == USER_ID

        ws.send_json({"type": "place", "x": 4, "y": 5, "color": "#008000"})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert error["code"] == "rate_limited"
        assert error["retryAfterSeconds"] > 0
