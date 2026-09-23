import bcrypt

from datetime import datetime

from app.database import get_connection


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def verify_password(
    password: str,
    password_hash: str
) -> bool:

    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def authenticate_user(
    nim: str,
    password: str
):
    connection = get_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE nim = ?
        """,
        (nim,)
    ).fetchone()

    connection.close()

    if not user:
        return None

    if not verify_password(
        password,
        user["password_hash"]
    ):
        return None

    return user