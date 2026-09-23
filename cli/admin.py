import sys
from getpass import getpass

from app.database import get_connection
from app.auth import hash_password
from app.config import (
    TELEGRAM_BOT_TOKEN,
    CAMPUS_LATITUDE,
    CAMPUS_LONGITUDE,
    CAMPUS_RADIUS,
    DATABASE_PATH
)


def create_user():
    print("\n--- Create New User ---")
    nim = input("NIM: ").strip()
    if not nim:
        print("NIM cannot be empty.")
        return

    name = input("Name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    password = getpass("Password: ")
    if not password:
        print("Password cannot be empty.")
        return

    hashed_pw = hash_password(password)

    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO users (
                nim, name, password_hash, created_at, updated_at
            ) VALUES (?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
            """,
            (nim, name, hashed_pw)
        )
        connection.commit()
        print(f"\nUser {name} (NIM: {nim}) created successfully!")
    except Exception as e:
        connection.rollback()
        print(f"\nError creating user: {e}")
    finally:
        connection.close()


def list_users():
    print("\n--- Registered Users ---")
    connection = get_connection()
    users = connection.execute(
        "SELECT id, nim, name, telegram_user_id FROM users ORDER BY nim"
    ).fetchall()
    connection.close()

    if not users:
        print("No users found.")
        return

    print(f"{'ID':<4} | {'NIM':<15} | {'NAME':<20} | {'TELEGRAM ID':<15}")
    print("-" * 65)
    for u in users:
        tel_id = u['telegram_user_id'] if u['telegram_user_id'] else "Not linked"
        print(f"{u['id']:<4} | {u['nim']:<15} | {u['name']:<20} | {tel_id:<15}")


def view_todays_attendance():
    print("\n--- Today's Attendance ---")
    connection = get_connection()
    records = connection.execute(
        """
        SELECT u.nim, u.name, a.check_in, a.latitude, a.longitude, a.distance, a.status
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        WHERE a.attendance_date = date('now', 'localtime')
        ORDER BY a.check_in DESC
        """
    ).fetchall()
    connection.close()

    if not records:
        print("No attendance records for today.")
        return

    print(f"{'NIM':<12} | {'NAME':<15} | {'TIME':<10} | {'LATITUDE':<12} | {'LONGITUDE':<12} | {'DISTANCE':<10} | {'STATUS':<10}")
    print("-" * 90)
    for r in records:
        print(f"{r['nim']:<12} | {r['name']:<15} | {r['check_in']:<10} | {r['latitude']:<12.6f} | {r['longitude']:<12.6f} | {r['distance']:<10.2f} | {r['status']:<10}")


def view_attendance_history():
    print("\n--- Attendance History ---")
    connection = get_connection()
    records = connection.execute(
        """
        SELECT u.nim, u.name, a.attendance_date, a.check_in, a.latitude, a.longitude, a.distance, a.status
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.attendance_date DESC, a.check_in DESC
        LIMIT 50
        """
    ).fetchall()
    connection.close()

    if not records:
        print("No attendance records found.")
        return

    print(f"{'DATE':<12} | {'NIM':<12} | {'NAME':<15} | {'TIME':<10} | {'LATITUDE':<12} | {'LONGITUDE':<12} | {'DIST (m)':<10} | {'STATUS':<10}")
    print("-" * 105)
    for r in records:
        print(f"{r['attendance_date']:<12} | {r['nim']:<12} | {r['name']:<15} | {r['check_in']:<10} | {r['latitude']:<12.6f} | {r['longitude']:<12.6f} | {r['distance']:<10.2f} | {r['status']:<10}")
    print("\n(Showing last 50 records)")


def system_information():
    print("\n--- System Information ---")
    print(f"Database Path    : {DATABASE_PATH}")
    print(f"Telegram Token   : {'Set' if TELEGRAM_BOT_TOKEN else 'Not Set'}")
    print(f"Campus Latitude  : {CAMPUS_LATITUDE}")
    print(f"Campus Longitude : {CAMPUS_LONGITUDE}")
    print(f"Campus Radius    : {CAMPUS_RADIUS} meters")
    
    connection = get_connection()
    user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    attendance_count = connection.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    connection.close()
    
    print(f"Total Users      : {user_count}")
    print(f"Total Attendance : {attendance_count} records")

