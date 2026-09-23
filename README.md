# Telegram Geofence Attendance System

## Project Overview
Sistem absensi berbasis Telegram menggunakan Geofencing. Aplikasi ini memungkinkan mahasiswa untuk login menggunakan NIM dan password melalui Telegram Bot, kemudian melakukan absensi dengan membagikan lokasi GPS. Sistem secara otomatis memverifikasi apakah mahasiswa berada dalam radius kampus yang telah ditentukan sebelum mencatat absensi. 

Dibangun murni menggunakan **Python full-stack/backend dan CLI**, tanpa framework web atau dependensi eksternal yang berat.

## Features
- **Autentikasi Aman:** Login dengan NIM dan password menggunakan enkripsi `bcrypt`.
- **Session Management:** Sesi Telegram terkait dengan user database.
- **Geofencing Absensi:** Verifikasi lokasi mahasiswa menggunakan formula Haversine untuk memastikan mereka berada dalam radius kampus.
- **Pencegahan Duplikasi:** Memastikan satu user hanya dapat melakukan absen satu kali setiap harinya.
- **CLI Admin:** Antarmuka baris perintah (CLI) bawaan untuk mengelola user dan melihat riwayat absensi.
- **Logging Terstruktur:** Setiap aksi penting akan dicatat untuk keperluan audit dan monitoring.

## Tech Stack
- Python 3.11+
- `python-telegram-bot` (Telegram Bot API wrapper)
- SQLite (Database bawaan)
- `bcrypt` (Password hashing)
- `python-dotenv` (Manajemen environment)
- `pytest` (Testing framework)

## Project Structure
```text
telegram-geofence-attendance/
│
├── app/                  # Core application modules
│   ├── __init__.py
│   ├── config.py         # Konfigurasi environment variables
│   ├── database.py       # Inisialisasi dan koneksi SQLite
│   ├── models.py         # (Reserved) Definisi struktur data
│   ├── auth.py           # Logika autentikasi dan hashing password
│   ├── location.py       # Perhitungan jarak Geofencing (Haversine)
│   ├── attendance.py     # Logika pencatatan absensi
│   └── bot.py            # Handler Telegram Bot 
│
├── cli/                  # Command Line Interface
│   ├── __init__.py
│   └── admin.py          # Fungsi-fungsi admin CLI
│
├── tests/                # Unit Testing (pytest)
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_location.py
│   └── test_attendance.py
│
├── data/                 # Folder penyimpanan database SQLite
│   └── .gitkeep
│
├── .env.example          # Template environment variable
├── .gitignore
├── requirements.txt      # Dependensi Python
├── main.py               # Entry point aplikasi (CLI & Bot Runner)
└── README.md
```

## Installation

1. Clone repository ini:
```bash
git clone <url-repository>
cd telegram-geofence-attendance
```

2. Buat dan aktifkan virtual environment:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependensi:
```bash
pip install -r requirements.txt
```

## Environment Configuration

Copy `.env.example` menjadi `.env`:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Buka `.env` dan atur variabel berikut:
```env
TELEGRAM_BOT_TOKEN=token_bot_anda_di_sini

CAMPUS_LATITUDE=-6.123456
CAMPUS_LONGITUDE=107.123456
CAMPUS_RADIUS=150

DATABASE_PATH=data/attendance.db
```

## Create Telegram Bot
1. Buka aplikasi Telegram dan cari **@BotFather**.
2. Kirim perintah `/newbot` dan ikuti instruksi untuk membuat bot baru.
3. BotFather akan memberikan sebuah **HTTP API Token**.
4. Salin token tersebut dan masukkan ke dalam file `.env` pada variabel `TELEGRAM_BOT_TOKEN`.

## Database
Aplikasi menggunakan **SQLite3**. Database secara otomatis dibuat dan diinisialisasi ketika Anda pertama kali menjalankan `main.py`.
File database akan tersimpan di dalam folder `data/` sesuai dengan variabel `DATABASE_PATH`.

## Running Application

Jalankan entry point utama aplikasi:
```bash
python main.py
```
Aplikasi akan menampilkan menu CLI interaktif. Pilih opsi `1` untuk menjalankan Telegram Bot.

## CLI Usage

Saat Anda menjalankan `python main.py`, Anda akan masuk ke CLI interaktif:
```text
========================================
 TELEGRAM GEOFENCING ATTENDANCE
========================================
1. Start Telegram Bot
2. Create User
3. List Users
4. View Today's Attendance
5. View Attendance History
6. System Information
0. Exit

Choose: 
```

**Keterangan Opsi Admin:**
- **Create User:** Daftarkan mahasiswa baru dengan mengisi NIM, Nama, dan Password. Password otomatis di-hash.
- **List Users:** Tampilkan semua mahasiswa yang telah didaftarkan beserta Telegram ID mereka (jika sudah login).
- **View Today's Attendance:** Lihat daftar absensi yang masuk hari ini.
- **View Attendance History:** Lihat 50 data absensi terakhir.

## Telegram Usage

Mahasiswa dapat mencari bot di Telegram dan menggunakan perintah berikut:

- `/start` - Menyapa pengguna dan memberikan arahan login.
- `/login` - Memulai alur autentikasi (Meminta NIM dan Password).
- `/absen` - Mengirim permintaan lokasi. Pengguna membagikan lokasi GPS menggunakan fitur "Send Location" di Telegram.
- `/status` - Melihat status absensi hari ini.
- `/logout` - Keluar dari sesi.
- `/help` - Menampilkan daftar perintah yang tersedia.

## Testing

Aplikasi dilengkapi dengan suite pengujian komprehensif menggunakan `pytest`.

Jalankan perintah berikut:
```bash
pytest -v
```

Cakupan pengujian meliputi:
- **Authentication:** Hashing password dan verifikasi kredensial.
- **Location:** Validasi formula Haversine dan toleransi jarak radius.
- **Attendance:** Pencatatan absensi yang valid dan penolakan pada entri duplikat di hari yang sama.

## Security Notes
- `TELEGRAM_BOT_TOKEN` dan `.env` tidak pernah dikomit ke repository Git.
- Password user tidak pernah disimpan sebagai plaintext, murni menggunakan `bcrypt`.
- Tidak ada query string interpolation (semua parameter menggunakan SQL bindings `(?, ?)`).
- Log (melalui module `logging`) tidak pernah mencatat password atau bot token.

## Geofencing Explanation
Sistem menggunakan **Formula Haversine** murni di dalam python (`math` library). Formula ini menghitung jarak _great-circle_ antara dua titik dalam bola, mengandalkan bujur dan lintang dari koordinat bumi. Jika hasil perhitungan (dalam meter) lebih kecil atau sama dengan `CAMPUS_RADIUS`, lokasi dianggap valid.

## Limitations
- Karena aplikasi mengandalkan GPS bawaan dari perangkat pengirim via Telegram, terdapat sedikit ketidakakuratan (drift) tergantung pada kualitas hardware smartphone pengguna.
- Aplikasi belum menangani skala timezone selain WIB (`Asia/Jakarta`).
- State / session handling bersifat _in-memory_, sehingga pengguna perlu `/login` ulang jika service bot di-restart.

## Future Improvements
- Persistent Telegram user sessions (misal menggunakan Redis atau simpan JWT).
- Pagination pada CLI Admin History.
- Integrasi ke sistem frontend dashboard absensi (jika skala ditingkatkan).
