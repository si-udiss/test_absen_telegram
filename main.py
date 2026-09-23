from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from app.config import TELEGRAM_BOT_TOKEN
from app.database import initialize_database


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "👋 Selamat datang di "
        "Telegram Attendance Bot!\n\n"
        "Gunakan /login untuk masuk."
    )


def main():

    initialize_database()

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN belum diset."
        )

    application = (
        Application
        .builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    print(
        "================================="
    )
    print(
        " Telegram Geofence Attendance"
    )
    print(
        "================================="
    )
    print(
        "Database : OK"
    )
    print(
        "Telegram : Starting..."
    )

    application.run_polling()


if __name__ == "__main__":
    main()