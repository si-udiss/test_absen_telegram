import sys
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

from telegram.ext import (
    Application,
    CommandHandler,
)

from app.config import TELEGRAM_BOT_TOKEN
from app.database import initialize_database
from app.bot import (
    start_command,
    help_command,
    logout_command,
    status_command,
    get_login_handler,
    get_absen_handler,
)

from cli.admin import (
    create_user,
    list_users,
    view_todays_attendance,
    view_attendance_history,
    system_information
)


def start_bot():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN belum diset.")
        return

    application = (
        Application
        .builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # ConversationHandler harus didaftarkan sebelum command biasa
    application.add_handler(get_login_handler())
    application.add_handler(get_absen_handler())

    application.add_handler(
        CommandHandler("start", start_command)
    )
    application.add_handler(
        CommandHandler("help", help_command)
    )
    application.add_handler(
        CommandHandler("logout", logout_command)
    )
    application.add_handler(
        CommandHandler("status", status_command)
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


def main():
    initialize_database()

    while True:
        print("\n========================================")
        print(" TELEGRAM GEOFENCING ATTENDANCE")
        print("========================================")
        print("1. Start Telegram Bot")
        print("2. Create User")
        print("3. List Users")
        print("4. View Today's Attendance")
        print("5. View Attendance History")
        print("6. System Information")
        print("0. Exit")
        
        choice = input("\nChoose: ").strip()

        if choice == '1':
            start_bot()
            break # Bot run_polling blocks, so if it exits, we probably want to exit the app
        elif choice == '2':
            create_user()
        elif choice == '3':
            list_users()
        elif choice == '4':
            view_todays_attendance()
        elif choice == '5':
            view_attendance_history()
        elif choice == '6':
            system_information()
        elif choice == '0':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()