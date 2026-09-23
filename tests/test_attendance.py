import pytest
from app.attendance import record_attendance, get_today_attendance
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
    # Create test user
    conn.execute(
        "INSERT INTO users (nim, name, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        ("12345", "Test User", "hash", "2026-01-01", "2026-01-01")
    )
    conn.commit()
    conn.close()
    
    yield
    
    try:
        os.remove(temp_path)
    except:
        pass


def test_user_dapat_absen():
    # User 1 absen pertama kali
    result = record_attendance(1, -6.123, 107.123, 50.5)
    assert result is not None
    assert result["status"] == "present"
    assert result["distance"] == 50.5


def test_data_attendance_tersimpan():
    record_attendance(1, -6.123, 107.123, 50.5)
    
    # Cek di database
    att = get_today_attendance(1)
    assert att is not None
    assert att["user_id"] == 1
    assert att["latitude"] == -6.123
    assert att["longitude"] == 107.123
    assert att["distance"] == 50.5
    assert att["status"] == "present"


def test_user_tidak_dapat_absen_dua_kali():
    # Absen pertama
    result1 = record_attendance(1, -6.123, 107.123, 50.5)
    assert result1 is not None
    
    # Absen kedua di hari yang sama
    result2 = record_attendance(1, -6.123, 107.123, 50.5)
    assert result2 is None  # Harus direject karena constraint duplikat
