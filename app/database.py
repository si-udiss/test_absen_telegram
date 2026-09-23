import sqlite3

from app.config import DATABASE_PATH


def get_connection():
    """Buat koneksi ke SQLite database.

    Otomatis membuat direktori parent jika belum ada.
    Foreign key constraint diaktifkan.
    """
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    # Aktifkan foreign key constraint
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """Inisialisasi database dan buat tabel jika belum ada.

    Tabel:
    - users: data mahasiswa (NIM, nama, password hash, telegram ID)
    - attendance: data absensi (tanggal, waktu, lokasi, jarak, status)

    Constraint:
    - users.nim UNIQUE
    - users.telegram_user_id UNIQUE (jika sudah terhubung)
    - attendance (user_id, attendance_date) UNIQUE — cegah duplikat absensi
    - attendance.user_id → users.id (foreign key)
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            telegram_user_id INTEGER UNIQUE,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            check_in TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            distance REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (user_id)
                REFERENCES users(id),

            UNIQUE (user_id, attendance_date)
        )
    """)

    connection.commit()
    connection.close()