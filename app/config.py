import os

from dotenv import load_dotenv


load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

CAMPUS_LATITUDE = float(
    os.getenv("CAMPUS_LATITUDE")
)

CAMPUS_LONGITUDE = float(
    os.getenv("CAMPUS_LONGITUDE")
)

CAMPUS_RADIUS = float(
    os.getenv("CAMPUS_RADIUS", 150)
)