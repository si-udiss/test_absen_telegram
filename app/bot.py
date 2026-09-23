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
#  Keyboards
# =============================================

def get_unauth_keyboard():
    return ReplyKeyboardMarkup(
        [["🔑 Login", "❓ Help"]],
        resize_keyboard=True
    )

def get_auth_keyboard():
    return ReplyKeyboardMarkup(
        [["📍 Absen", "📋 Status"], ["🚪 Logout"]],
        resize_keyboard=True
    )


# =============================================
#  /start
# =============================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handler untuk /start command."""
    telegram_user_id = update.effective_user.id
    
    if telegram_user_id in authenticated_users:
        await update.message.reply_text(
            "\U0001f44b Selamat datang kembali di "
            "Telegram Attendance Bot.\n\n"
            "Gunakan menu di bawah ini untuk berinteraksi.",
            reply_markup=get_auth_keyboard()
        )
    else:
        await update.message.reply_text(
            "\U0001f44b Selamat datang di "
            "Telegram Attendance Bot.\n\n"
            "Silakan gunakan tombol Login untuk masuk.",
            reply_markup=get_unauth_keyboard()
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
            "Gunakan Logout untuk keluar terlebih dahulu.",
            reply_markup=get_auth_keyboard()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Masukkan NIM kamu:",
        reply_markup=ReplyKeyboardRemove()
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
                "Gunakan Login untuk mencoba lagi."
            ),
            reply_markup=get_unauth_keyboard()
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
            "Gunakan tombol Absen untuk melakukan absensi."
        ),
        reply_markup=get_auth_keyboard()
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
        reply_markup=get_unauth_keyboard()
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
            "\u2139\ufe0f Kamu belum login.",
            reply_markup=get_unauth_keyboard()
        )
        return

    del authenticated_users[telegram_user_id]

    logger.info(
        "User logout: telegram_id=%s",
        telegram_user_id
    )

    await update.message.reply_text(
        "\u2705 Kamu telah logout.",
        reply_markup=get_unauth_keyboard()
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
            "Gunakan tombol Login.",
            reply_markup=get_unauth_keyboard()
        )
        return ConversationHandler.END

    user_id = authenticated_users[telegram_user_id]

    # Cek duplikat absensi hari ini
    existing = get_today_attendance(user_id)
    if existing:
        await update.message.reply_text(
            "\u26a0\ufe0f Kamu sudah melakukan "
            "absensi hari ini.\n\n"
            f"Waktu: {existing['check_in']}",
            reply_markup=get_auth_keyboard()
        )
        return ConversationHandler.END

    # Minta lokasi dengan keyboard button
    location_button = KeyboardButton(
        text="\U0001f4cd Kirim Lokasi",
        request_location=True
    )
    # Tambahkan tombol batal
    cancel_button = KeyboardButton(text="❌ Batal Absen")
    
    reply_markup = ReplyKeyboardMarkup(
        [[location_button], [cancel_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "\U0001f4cd VERIFIKASI LOKASI\n\n"
        "Silakan bagikan lokasi kamu menggunakan "
        'tombol "Kirim Lokasi" di bawah ini.\n\n'
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
            "Silakan login kembali.",
            reply_markup=get_unauth_keyboard()
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
            reply_markup=get_auth_keyboard()
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
            reply_markup=get_auth_keyboard()
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
        reply_markup=get_auth_keyboard()
    )

    return ConversationHandler.END


async def absen_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Batalkan proses absensi."""
    # Check session to return proper keyboard
    telegram_user_id = update.effective_user.id
    keyboard = get_auth_keyboard() if telegram_user_id in authenticated_users else get_unauth_keyboard()
    
    await update.message.reply_text(
        "Absensi dibatalkan.",
        reply_markup=keyboard
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
            "\u274c Kamu belum login.",
            reply_markup=get_unauth_keyboard()
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
            "\u274c Data user tidak ditemukan.",
            reply_markup=get_unauth_keyboard()
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
            f"Jarak: {attendance['distance']} meter",
            reply_markup=get_auth_keyboard()
        )
    else:
        await update.message.reply_text(
            "\U0001f4cb STATUS ABSENSI\n\n"
            f"Nama: {user['name']}\n"
            f"NIM: {user['nim']}\n\n"
            "Status hari ini:\n"
            "\u274c Belum absen",
            reply_markup=get_auth_keyboard()
        )


# =============================================
#  Handler factories & Registration
# =============================================

def register_handlers(application):
    """Daftarkan semua handler bot dengan dukungan Regex Keyboard."""
    
    # 1. Login Conversation
    login_conv = ConversationHandler(
        entry_points=[
            CommandHandler("login", login_start),
            MessageHandler(filters.Regex(r"^(🔑 Login|/login)$"), login_start)
        ],
        states={
            WAITING_NIM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_nim)
            ],
            WAITING_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", login_cancel)
        ],
    )
    application.add_handler(login_conv)

    # 2. Absen Conversation
    absen_conv = ConversationHandler(
        entry_points=[
            CommandHandler("absen", absen_start),
            MessageHandler(filters.Regex(r"^(📍 Absen|/absen)$"), absen_start)
        ],
        states={
            WAITING_LOCATION: [
                MessageHandler(filters.LOCATION, absen_location)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", absen_cancel),
            MessageHandler(filters.Regex(r"^(❌ Batal Absen)$"), absen_cancel)
        ],
    )
    application.add_handler(absen_conv)

    # 3. Standard Commands & Buttons
    application.add_handler(CommandHandler("start", start_command))
    
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Regex(r"^(❓ Help)$"), help_command))

    application.add_handler(CommandHandler("logout", logout_command))
    application.add_handler(MessageHandler(filters.Regex(r"^(🚪 Logout)$"), logout_command))

    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.Regex(r"^(📋 Status)$"), status_command))
