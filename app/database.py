import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/attendance.db")


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nim TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            telegram_user_id INTEGER UNIQUE,
            created_at TEXT NOT NULL
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
                REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()