import logging

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.auth import authenticate_user
from app.database import get_connection
from app.location import calculate_distance
from app.attendance import (
    get_today_attendance,
    record_attendance,
)
from app.config import (
    CAMPUS_LATITUDE,
    CAMPUS_LONGITUDE,
    CAMPUS_RADIUS,
)


logger = logging.getLogger(__name__)

# ConversationHandler states — Login
WAITING_NIM = 0
WAITING_PASSWORD = 1

# ConversationHandler states — Absen
WAITING_LOCATION = 0

# In-memory session: {telegram_user_id: database_user_id}
authenticated_users = {}


# =============================================
#  /start
# =============================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handler untuk /start command."""
    await update.message.reply_text(
        "\U0001f44b Selamat datang di "
        "Telegram Attendance Bot.\n\n"
        "Silakan gunakan /login untuk masuk."
    )


# =============================================
#  /help
# =============================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handler untuk /help command."""
    await update.message.reply_text(
        "/start  - Memulai bot\n"
        "/login  - Login menggunakan NIM dan password\n"
        "/logout - Logout\n"
        "/absen  - Melakukan absensi\n"
        "/status - Melihat status absensi hari ini\n"
        "/help   - Melihat bantuan"
    )


# =============================================
#  /login — ConversationHandler
# =============================================

async def login_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Mulai flow login. Minta NIM."""
    telegram_user_id = update.effective_user.id

    if telegram_user_id in authenticated_users:
        await update.message.reply_text(
            "\u2139\ufe0f Kamu sudah login.\n\n"
            "Gunakan /logout untuk keluar terlebih dahulu."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Masukkan NIM kamu:"
    )
    return WAITING_NIM


async def login_nim(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Terima NIM, minta password."""
    nim = update.message.text.strip()
    context.user_data["login_nim"] = nim

    await update.message.reply_text(
        "Masukkan password:"
    )
    return WAITING_PASSWORD


async def login_password(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Terima password, verifikasi login."""
    nim = context.user_data.get("login_nim", "")
    password = update.message.text.strip()
    telegram_user_id = update.effective_user.id

    # Hapus pesan password dari chat (best effort)
    try:
        await update.message.delete()
    except Exception:
        pass

    user = authenticate_user(nim, password)

    if user is None:
        logger.warning(
            "Login gagal untuk NIM: %s", nim
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "\u274c Login gagal.\n\n"
                "NIM atau password salah.\n"
                "Gunakan /login untuk mencoba lagi."
            )
        )
        context.user_data.pop("login_nim", None)
        return ConversationHandler.END

    # Hubungkan telegram_user_id dengan user
    connection = get_connection()
    connection.execute(
        """
        UPDATE users
        SET telegram_user_id = ?,
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """,
        (telegram_user_id, user["id"])
    )
    connection.commit()
    connection.close()

    # Simpan session
    authenticated_users[telegram_user_id] = user["id"]

    logger.info(
        "Login berhasil: %s (%s)",
        user["name"], nim
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "\u2705 Login berhasil.\n\n"
            f"Nama: {user['name']}\n"
            f"NIM: {user['nim']}\n\n"
            "Gunakan /absen untuk melakukan absensi."
        )
    )

    context.user_data.pop("login_nim", None)
    return ConversationHandler.END


async def login_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Batalkan proses login."""
    context.user_data.pop("login_nim", None)
    await update.message.reply_text(
        "Login dibatalkan.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# =============================================
#  /logout
# =============================================

async def logout_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handler untuk /logout command."""
    telegram_user_id = update.effective_user.id

    if telegram_user_id not in authenticated_users:
        await update.message.reply_text(
            "\u2139\ufe0f Kamu belum login."
        )
        return

    del authenticated_users[telegram_user_id]

    logger.info(
        "User logout: telegram_id=%s",
        telegram_user_id
    )

    await update.message.reply_text(
        "\u2705 Kamu telah logout."
    )


# =============================================
#  /absen — ConversationHandler
# =============================================

async def absen_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Mulai flow absensi. Cek login, cek duplikat, minta lokasi."""
    telegram_user_id = update.effective_user.id

    # Cek login
    if telegram_user_id not in authenticated_users:
        await update.message.reply_text(
            "\u274c Kamu harus login terlebih dahulu.\n\n"
            "Gunakan /login."
        )
        return ConversationHandler.END

    user_id = authenticated_users[telegram_user_id]

    # Cek duplikat absensi hari ini
    existing = get_today_attendance(user_id)
    if existing:
        await update.message.reply_text(
            "\u26a0\ufe0f Kamu sudah melakukan "
            "absensi hari ini.\n\n"
            f"Waktu: {existing['check_in']}"
        )
        return ConversationHandler.END

    # Minta lokasi dengan keyboard button
    location_button = KeyboardButton(
        text="\U0001f4cd Kirim Lokasi",
        request_location=True
    )
    reply_markup = ReplyKeyboardMarkup(
        [[location_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "\U0001f4cd VERIFIKASI LOKASI\n\n"
        "Silakan bagikan lokasi kamu menggunakan "
        'fitur "Send Location" Telegram.\n\n'
        "Lokasi harus berada dalam radius "
        f"{int(CAMPUS_RADIUS)} meter dari kampus.",
        reply_markup=reply_markup
    )

    return WAITING_LOCATION


async def absen_location(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Terima lokasi, hitung jarak, catat absensi."""
    telegram_user_id = update.effective_user.id
    user_id = authenticated_users.get(telegram_user_id)

    if user_id is None:
        await update.message.reply_text(
            "\u274c Session tidak valid. "
            "Silakan /login kembali.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    location = update.message.location
    latitude = location.latitude
    longitude = location.longitude

    logger.info(
        "Location received: user_id=%s, "
        "lat=%s, lon=%s",
        user_id, latitude, longitude
    )

    # Hitung jarak dari kampus
    distance = calculate_distance(
        latitude, longitude,
        CAMPUS_LATITUDE, CAMPUS_LONGITUDE
    )

    # Cek apakah dalam radius
    if distance > CAMPUS_RADIUS:
        logger.info(
            "Attendance rejected: user_id=%s, "
            "distance=%.2fm (max=%sm)",
            user_id, distance, CAMPUS_RADIUS
        )
        await update.message.reply_text(
            "\u274c Absensi ditolak.\n\n"
            "Kamu berada di luar area kampus.\n\n"
            f"Jarak: {distance:.2f} meter\n"
            f"Radius maksimum: {int(CAMPUS_RADIUS)}"
            " meter",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    # Catat absensi
    result = record_attendance(
        user_id, latitude, longitude, distance
    )

    if result is None:
        # Duplikat (race condition guard)
        existing = get_today_attendance(user_id)
        await update.message.reply_text(
            "\u26a0\ufe0f Kamu sudah melakukan "
            "absensi hari ini.\n\n"
            f"Waktu: {existing['check_in'] if existing else '-'}",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    logger.info(
        "Attendance accepted: user_id=%s, "
        "distance=%.2fm",
        user_id, distance
    )

    await update.message.reply_text(
        "\U0001f4cd Lokasi terverifikasi.\n\n"
        f"Jarak dari kampus: {distance:.2f} meter\n"
        f"Radius maksimum: {int(CAMPUS_RADIUS)}"
        " meter\n\n"
        "\u2705 Absensi berhasil dicatat!\n\n"
        f"Waktu: {result['check_in']}\n"
        f"Status: {result['status']}",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


async def absen_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Batalkan proses absensi."""
    await update.message.reply_text(
        "Absensi dibatalkan.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# =============================================
#  /status
# =============================================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handler untuk /status command."""
    telegram_user_id = update.effective_user.id

    if telegram_user_id not in authenticated_users:
        await update.message.reply_text(
            "\u274c Kamu belum login."
        )
        return

    user_id = authenticated_users[telegram_user_id]

    # Ambil data user
    connection = get_connection()
    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    connection.close()

    if not user:
        await update.message.reply_text(
            "\u274c Data user tidak ditemukan."
        )
        return

    # Cek absensi hari ini
    attendance = get_today_attendance(user_id)

    if attendance:
        await update.message.reply_text(
            "\U0001f4cb STATUS ABSENSI\n\n"
            f"Nama: {user['name']}\n"
            f"NIM: {user['nim']}\n\n"
            "Status:\n"
            "\u2705 Sudah absen\n\n"
            f"Waktu: {attendance['check_in']}\n"
            f"Jarak: {attendance['distance']} meter"
        )
    else:
        await update.message.reply_text(
            "\U0001f4cb STATUS ABSENSI\n\n"
            f"Nama: {user['name']}\n"
            f"NIM: {user['nim']}\n\n"
            "Status hari ini:\n"
            "\u274c Belum absen"
        )


# =============================================
#  Handler factories
# =============================================

def get_login_handler():
    """Buat ConversationHandler untuk flow login."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("login", login_start)
        ],
        states={
            WAITING_NIM: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    login_nim
                )
            ],
            WAITING_PASSWORD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    login_password
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", login_cancel)
        ],
    )


def get_absen_handler():
    """Buat ConversationHandler untuk flow absensi."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("absen", absen_start)
        ],
        states={
            WAITING_LOCATION: [
                MessageHandler(
                    filters.LOCATION,
                    absen_location
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", absen_cancel)
        ],
    )
