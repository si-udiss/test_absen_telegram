import logging

from datetime import datetime, timezone, timedelta

from app.database import get_connection

logger = logging.getLogger(__name__)

# Timezone Asia/Jakarta (UTC+7)
WIB = timezone(timedelta(hours=7))


def get_today_wib():
    """Dapatkan tanggal hari ini dalam WIB."""
    return datetime.now(WIB).strftime("%Y-%m-%d")


def get_time_wib():
    """Dapatkan waktu sekarang dalam WIB."""
    return datetime.now(WIB).strftime("%H:%M:%S")


def get_today_attendance(user_id):
    """Cek apakah user sudah absen hari ini.

    Returns:
        sqlite3.Row atau None
    """
    today = get_today_wib()
    connection = get_connection()

    attendance = connection.execute(
        """
        SELECT *
        FROM attendance
        WHERE user_id = ?
        AND attendance_date = ?
        """,
        (user_id, today)
    ).fetchone()

    connection.close()
    return attendance


def record_attendance(
    user_id,
    latitude,
    longitude,
    distance
):
    """Catat absensi ke database.

    Args:
        user_id: ID user dari tabel users
        latitude: Latitude lokasi user
        longitude: Longitude lokasi user
        distance: Jarak dari kampus (meter)

    Returns:
        dict dengan info attendance, atau None jika duplikat

    Raises:
        sqlite3.IntegrityError jika duplikat (constraint level)
    """
    today = get_today_wib()
    check_in = get_time_wib()
    now = datetime.now(WIB).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO attendance (
                user_id,
                attendance_date,
                check_in,
                latitude,
                longitude,
                distance,
                status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                today,
                check_in,
                latitude,
                longitude,
                round(distance, 2),
                "present",
                now,
            )
        )
        connection.commit()

        logger.info(
            "Attendance recorded: user_id=%s, "
            "date=%s, distance=%.2fm",
            user_id, today, distance
        )

        return {
            "attendance_date": today,
            "check_in": check_in,
            "distance": round(distance, 2),
            "status": "present",
        }

    except Exception as e:
        connection.rollback()
        logger.warning(
            "Duplicate attendance: user_id=%s, "
            "date=%s — %s",
            user_id, today, e
        )
        return None

    finally:
        connection.close()
