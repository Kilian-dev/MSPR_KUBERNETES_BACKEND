import json
import os
import importlib.util
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

load_dotenv()


# ── helpers ───────────────────────────────────────────────────────────────────

def load_handler(func_dir):
    path = os.path.join(
        os.path.dirname(__file__), "..", func_dir, "function", "handler.py"
    )
    spec = importlib.util.spec_from_file_location(f"{func_dir}_handler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mock_secret(name):
    return {
        "host":     os.getenv("DB_HOST", "localhost"),
        "port":     os.getenv("DB_PORT", "5432"),
        "dbname":   os.getenv("DB_NAME", "MSPR_2"),
        "user":     os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }[name]


class Event:
    def __init__(self, body):
        self.body = json.dumps(body).encode()


class Context:
    hostname = "test"


gp   = load_handler("generate-password")
g2fa = load_handler("generate-2fa")
auth = load_handler("authenticate")
renew = load_handler("renew-credentials")


# ── generate-password ─────────────────────────────────────────────────────────

def test_generate_password_missing_username():
    with patch.object(gp, "read_secret", side_effect=mock_secret):
        resp = gp.handle(Event({}), Context())
        assert resp["statusCode"] == 400

def test_generate_password_success():
    with patch.object(gp, "read_secret", side_effect=mock_secret):
        resp = gp.handle(Event({"username": "ci_test_user"}), Context())
        body = json.loads(resp["body"])
        assert resp["statusCode"] == 200
        assert body["success"] is True
        assert "password" in body
        assert "password_qr_code" in body

def test_generate_password_duplicate():
    with patch.object(gp, "read_secret", side_effect=mock_secret):
        resp = gp.handle(Event({"username": "ci_test_user"}), Context())
        assert resp["statusCode"] == 409


# ── generate-2fa ──────────────────────────────────────────────────────────────

def test_generate_2fa_missing_username():
    with patch.object(g2fa, "read_secret", side_effect=mock_secret):
        resp = g2fa.handle(Event({}), Context())
        assert resp["statusCode"] == 400

def test_generate_2fa_user_not_found():
    with patch.object(g2fa, "read_secret", side_effect=mock_secret):
        resp = g2fa.handle(Event({"username": "nobody_xyz_404"}), Context())
        assert resp["statusCode"] == 404

def test_generate_2fa_success():
    with patch.object(g2fa, "read_secret", side_effect=mock_secret):
        resp = g2fa.handle(Event({"username": "ci_test_user"}), Context())
        body = json.loads(resp["body"])
        assert resp["statusCode"] == 200
        assert "mfa_secret" in body
        assert "mfa_qr_code" in body


# ── authenticate ──────────────────────────────────────────────────────────────

def test_authenticate_missing_fields():
    with patch.object(auth, "read_secret", side_effect=mock_secret):
        resp = auth.handle(Event({"username": "ci_test_user"}), Context())
        assert resp["statusCode"] == 400

def test_authenticate_user_not_found():
    with patch.object(auth, "read_secret", side_effect=mock_secret):
        resp = auth.handle(Event({
            "username": "nobody_xyz_404",
            "password": "x",
            "totp_code": "000000"
        }), Context())
        assert resp["statusCode"] == 404

def test_authenticate_wrong_password():
    with patch.object(auth, "read_secret", side_effect=mock_secret):
        resp = auth.handle(Event({
            "username": "ci_test_user",
            "password": "mauvais_mdp",
            "totp_code": "000000"
        }), Context())
        assert resp["statusCode"] == 401


# ── renew-credentials ─────────────────────────────────────────────────────────

def test_renew_missing_username():
    with patch.object(renew, "read_secret", side_effect=mock_secret):
        resp = renew.handle(Event({}), Context())
        assert resp["statusCode"] == 400

def test_renew_user_not_found():
    with patch.object(renew, "read_secret", side_effect=mock_secret):
        resp = renew.handle(Event({"username": "nobody_xyz_404"}), Context())
        assert resp["statusCode"] == 404

def test_renew_success():
    with patch.object(renew, "read_secret", side_effect=mock_secret):
        resp = renew.handle(Event({"username": "ci_test_user"}), Context())
        body = json.loads(resp["body"])
        assert resp["statusCode"] == 200
        assert body["success"] is True
        assert "password" in body
        assert "mfa_secret" in body
