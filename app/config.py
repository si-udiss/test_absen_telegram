import os

from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", "data/attendance.db")
)

CAMPUS_LATITUDE = float(
    os.getenv("CAMPUS_LATITUDE", 0)
)

CAMPUS_LONGITUDE = float(
    os.getenv("CAMPUS_LONGITUDE", 0)
)

CAMPUS_RADIUS = float(
    os.getenv("CAMPUS_RADIUS", 150)
)