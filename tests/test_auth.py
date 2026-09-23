import pytest
from app.auth import hash_password, verify_password, authenticate_user
from app.database import get_connection, initialize_database
import os
import tempfile
from pathlib import Path


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    fd, temp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db_path = Path(temp_path)
    monkeypatch.setattr("app.database.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.config.DATABASE_PATH", db_path)
    
    initialize_database()
    
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (nim, name, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        ("12345", "Test User", hash_password("password123"), "2026-01-01", "2026-01-01")
    )
    conn.commit()
    conn.close()
    
    yield
    
    try:
        os.remove(temp_path)
    except:
        pass


def test_password_hashing():
    pw = "secret"
    hashed = hash_password(pw)
    assert hashed != pw
    assert hashed.startswith("$2")


def test_password_verification_benar():
    pw = "secret"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True


def test_password_verification_salah():
    pw = "secret"
    hashed = hash_password(pw)
    assert verify_password("wrong", hashed) is False


def test_login_dengan_nim_valid():
    user = authenticate_user("12345", "password123")
    assert user is not None
    assert user["nim"] == "12345"


def test_login_dengan_nim_tidak_valid():
    user = authenticate_user("99999", "password123")
    assert user is None


def test_login_dengan_password_salah():
    user = authenticate_user("12345", "wrongpass")
    assert user is None
