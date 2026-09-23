# Project: Telegram Geofencing Attendance System

Saya ingin membangun aplikasi absensi berbasis Telegram dengan **Python full-stack/backend dan CLI**, tanpa Laravel, FastAPI, frontend web, atau framework JavaScript.

Tujuan aplikasi:

> Mahasiswa login menggunakan NIM dan password melalui Telegram Bot, kemudian melakukan absensi dengan membagikan lokasi GPS. Sistem memeriksa apakah lokasi mahasiswa berada dalam radius lingkungan kampus. Jika berada di dalam radius dan memenuhi aturan absensi, sistem mencatat absensi ke database.

Jangan menggunakan face recognition.

---

## 1. Tech Stack

Gunakan:

* Python 3.11+
* `python-telegram-bot`
* SQLite
* `bcrypt` untuk password hashing
* `python-dotenv`
* Python standard library `math` untuk perhitungan Haversine
* `pytest` untuk testing

Hindari dependency yang tidak diperlukan.

Tidak perlu:

* Laravel
* Django
* Flask
* FastAPI
* React
* Vue
* Next.js
* HTML/CSS/JS
* face recognition
* external geolocation API

---

# 2. Struktur Project

Gunakan struktur modular berikut:

```text
telegram-geofence-attendance/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── auth.py
│   ├── location.py
│   ├── attendance.py
│   └── bot.py
│
├── cli/
│   ├── __init__.py
│   └── admin.py
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_location.py
│   └── test_attendance.py
│
├── data/
│   └── .gitkeep
│
├── .env.example
├── .gitignore
├── requirements.txt
├── main.py
└── README.md
```

Jika ada kebutuhan perubahan struktur, jelaskan alasannya sebelum mengubah struktur utama.

---

# 3. Environment Configuration

Gunakan `.env`.

`.env.example` harus berisi:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here

CAMPUS_LATITUDE=-6.000000
CAMPUS_LONGITUDE=107.000000
CAMPUS_RADIUS=150

DATABASE_PATH=data/attendance.db
```

Jangan pernah hardcode Telegram Bot Token.

`.env` harus masuk `.gitignore`.

---

# 4. Database

Gunakan SQLite.

Database harus otomatis dibuat ketika aplikasi pertama kali dijalankan.

Buat tabel:

## users

```text
id
nim
name
password_hash
telegram_user_id
created_at
updated_at
```

Ketentuan:

* `id` primary key
* `nim` unique
* `telegram_user_id` unique jika sudah terhubung
* password tidak boleh disimpan plaintext

## attendance

```text
id
user_id
attendance_date
check_in
latitude
longitude
distance
status
created_at
```

Foreign key:

```text
attendance.user_id → users.id
```

Aktifkan SQLite foreign key constraint.

Tambahkan unique constraint agar satu user tidak dapat membuat lebih dari satu absensi masuk pada tanggal yang sama.

---

# 5. Authentication

Buat sistem autentikasi menggunakan NIM dan password.

Gunakan bcrypt.

Fungsi minimal:

```python
hash_password(password)
verify_password(password, password_hash)
authenticate_user(nim, password)
```

Password harus selalu diverifikasi menggunakan hash.

Jangan menyimpan password plaintext.

---

# 6. Telegram User Session

Setelah user berhasil login:

```text
Telegram User ID
        ↓
Database User
        ↓
Authenticated Session
```

Untuk MVP, session boleh disimpan di memory aplikasi menggunakan dictionary.

Contoh konsep:

```python
authenticated_users = {
    telegram_user_id: database_user_id
}
```

Jika bot restart, user harus login kembali.

Pastikan user tidak dapat menjalankan `/absen` sebelum login.

---

# 7. Telegram Commands

Implementasikan command berikut:

```text
/start
/login
/logout
/absen
/status
/help
```

## `/start`

Menampilkan:

```text
👋 Selamat datang di Telegram Attendance Bot.

Silakan gunakan /login untuk masuk.
```

## `/login`

Flow:

```text
/login
↓
Bot meminta NIM
↓
User memasukkan NIM
↓
Bot meminta password
↓
User memasukkan password
↓
Sistem melakukan verifikasi bcrypt
↓
Login berhasil / gagal
```

Gunakan Telegram ConversationHandler atau mekanisme state yang sesuai.

Password yang dikirim user jangan ditampilkan kembali oleh bot.

Setelah berhasil:

```text
✅ Login berhasil.

Nama: {name}
NIM: {nim}

Gunakan /absen untuk melakukan absensi.
```

Hubungkan `telegram_user_id` dengan akun user ketika login berhasil.

---

# 8. `/logout`

Hapus session user dari memory.

Response:

```text
✅ Kamu telah logout.
```

Jika belum login:

```text
ℹ️ Kamu belum login.
```

---

# 9. `/absen`

User harus sudah login.

Jika belum:

```text
❌ Kamu harus login terlebih dahulu.

Gunakan /login.
```

Jika sudah login:

Bot meminta lokasi:

```text
📍 VERIFIKASI LOKASI

Silakan bagikan lokasi kamu menggunakan fitur
"Send Location" Telegram.

Lokasi harus berada dalam radius
{CAMPUS_RADIUS} meter dari kampus.
```

Gunakan Telegram location request/reply keyboard yang sesuai.

---

# 10. Location Handler

Bot harus menangani Telegram Location message.

Ambil:

```python
latitude
longitude
```

dari pesan Telegram.

Jangan meminta user mengetik latitude/longitude secara manual.

Setelah lokasi diterima:

```text
Telegram Location
        ↓
latitude + longitude
        ↓
calculate_distance()
        ↓
bandingkan dengan CAMPUS_RADIUS
```

---

# 11. Haversine

Implementasikan fungsi:

```python
calculate_distance(
    latitude1,
    longitude1,
    latitude2,
    longitude2
)
```

Return jarak dalam meter.

Gunakan:

```text
Earth radius = 6,371,000 meters
```

Tidak perlu Google Maps API atau API lokasi eksternal.

---

# 12. Geofencing

Bandingkan:

```text
distance <= CAMPUS_RADIUS
```

Jika true:

```text
Lokasi valid
```

Jika false:

```text
Lokasi di luar area kampus
```

Contoh response jika valid:

```text
📍 Lokasi terverifikasi.

Jarak dari kampus: 83.42 meter
Radius maksimum: 150 meter
```

Jika tidak valid:

```text
❌ Absensi ditolak.

Kamu berada di luar area kampus.

Jarak: 842.31 meter
Radius maksimum: 150 meter
```

Jangan mencatat absensi jika lokasi berada di luar radius.

---

# 13. Attendance Service

Buat fungsi/service khusus untuk absensi.

Minimal:

```python
record_attendance(
    user_id,
    latitude,
    longitude,
    distance
)
```

Status awal:

```text
present
```

Simpan:

* user_id
* tanggal
* waktu check-in
* latitude
* longitude
* distance
* status

Gunakan timezone:

```text
Asia/Jakarta
```

Jangan menggunakan UTC untuk tampilan waktu absensi.

---

# 14. Prevent Duplicate Attendance

User hanya boleh melakukan absensi masuk satu kali per hari.

Jika user sudah absen:

```text
⚠️ Kamu sudah melakukan absensi hari ini.

Waktu: 07:42:31
```

Jangan membuat record kedua.

Gunakan database constraint dan pengecekan application-level.

Jangan hanya mengandalkan pengecekan Python karena race condition masih mungkin terjadi.

---

# 15. `/status`

Jika belum login:

```text
❌ Kamu belum login.
```

Jika sudah login tetapi belum absen:

```text
📋 STATUS ABSENSI

Nama: {name}
NIM: {nim}

Status hari ini:
❌ Belum absen
```

Jika sudah absen:

```text
📋 STATUS ABSENSI

Nama: {name}
NIM: {nim}

Status:
✅ Sudah absen

Waktu: 07:42:31
Jarak: 83.42 meter
```

---

# 16. `/help`

Tampilkan command:

```text
/start  - Memulai bot
/login  - Login menggunakan NIM dan password
/logout - Logout
/absen  - Melakukan absensi
/status - Melihat status absensi hari ini
/help   - Melihat bantuan
```

---

# 17. CLI Admin

Project harus tetap memiliki CLI sederhana.

Jalankan:

```bash
python main.py
```

Sediakan menu:

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

## Create User

Admin dapat membuat:

```text
NIM
Nama
Password
```

Password harus langsung di-hash menggunakan bcrypt.

Jangan pernah menampilkan password hash kepada user biasa.

---

# 18. CLI List Users

Tampilkan minimal:

```text
ID | NIM | NAME | TELEGRAM ID
```

Jangan tampilkan password hash.

---

# 19. CLI Attendance

Admin dapat melihat:

```text
NIM
Name
Date
Check-in
Latitude
Longitude
Distance
Status
```

---

# 20. Logging

Gunakan Python `logging`.

Log minimal:

```text
Bot started
User login success
User login failed
Location received
Attendance accepted
Attendance rejected
Duplicate attendance
Bot error
```

Jangan log:

* password
* password hash
* Telegram bot token

---

# 21. Error Handling

Bot tidak boleh crash hanya karena user mengirim input yang salah.

Tangani:

* NIM tidak ditemukan
* password salah
* user belum login
* user sudah login
* lokasi tidak dikirim
* database error
* Telegram API error
* malformed input
* duplicate attendance

Untuk error internal, berikan pesan umum kepada user dan simpan detailnya di log.

Jangan membocorkan stack trace kepada user.

---

# 22. Security

Terapkan minimal:

* `.env` untuk secrets
* bcrypt untuk password
* parameterized SQL queries
* jangan log password
* jangan log bot token
* jangan tampilkan password
* validasi input
* session berdasarkan Telegram User ID
* user hanya dapat melihat data absensinya sendiri melalui bot

Jangan menggunakan SQL string interpolation.

Contoh yang benar:

```python
connection.execute(
    "SELECT * FROM users WHERE nim = ?",
    (nim,)
)
```

---

# 23. Testing

Gunakan pytest.

Test minimal:

### Authentication

* password hashing
* password verification benar
* password verification salah
* login dengan NIM valid
* login dengan NIM tidak valid

### Geolocation

Test:

* dua koordinat yang sama → jarak mendekati 0
* koordinat di dalam radius
* koordinat di luar radius
* perhitungan meter masuk akal

### Attendance

Test:

* user dapat absen
* user tidak dapat absen dua kali pada tanggal yang sama
* user di luar radius ditolak
* data attendance tersimpan dengan benar

---

# 24. README

Buat README lengkap dengan:

```text
Project Overview
Features
Tech Stack
Project Structure
Installation
Environment Configuration
Create Telegram Bot
Database
Running Application
CLI Usage
Telegram Usage
Testing
Security Notes
Geofencing Explanation
Limitations
Future Improvements
```

Berikan contoh:

```bash
git clone ...
cd telegram-geofence-attendance

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env

python main.py
```

---

# 25. Acceptance Criteria

Anggap implementasi selesai hanya jika semua poin berikut terpenuhi:

* [ ] Project dapat dijalankan dengan `python main.py`
* [ ] SQLite database otomatis dibuat
* [ ] Telegram bot berhasil connect
* [ ] `/start` bekerja
* [ ] `/login` bekerja
* [ ] NIM dan password dapat diverifikasi
* [ ] Password disimpan menggunakan bcrypt
* [ ] Telegram User ID dikaitkan dengan user
* [ ] `/logout` bekerja
* [ ] `/absen` hanya dapat digunakan setelah login
* [ ] Bot dapat menerima Telegram Location
* [ ] Latitude dan longitude berhasil dibaca
* [ ] Haversine distance berhasil dihitung
* [ ] Radius kampus dapat dikonfigurasi melalui `.env`
* [ ] Lokasi di dalam radius diterima
* [ ] Lokasi di luar radius ditolak
* [ ] Attendance tersimpan ke SQLite
* [ ] Duplicate attendance dicegah
* [ ] `/status` menampilkan status absensi hari ini
* [ ] `/help` bekerja
* [ ] CLI admin dapat membuat user
* [ ] CLI admin dapat melihat user
* [ ] CLI admin dapat melihat attendance
* [ ] Logging diterapkan
* [ ] Error handling diterapkan
* [ ] Unit test tersedia
* [ ] Semua test berhasil
* [ ] README lengkap
* [ ] `.env` tidak masuk Git
* [ ] Password tidak pernah disimpan plaintext
* [ ] Bot token tidak pernah hardcode

---

# 26. Development Rules

Kerjakan secara bertahap, jangan langsung membuat seluruh fitur sekaligus.

Urutan implementasi:

### Phase 1 — Foundation

1. Project structure
2. Virtual environment
3. requirements.txt
4. `.env.example`
5. config
6. SQLite
7. models/database initialization

### Phase 2 — Telegram

8. Telegram Bot connection
9. `/start`
10. `/help`

### Phase 3 — Authentication

11. User creation
12. bcrypt
13. `/login`
14. Telegram session
15. `/logout`

### Phase 4 — Geofencing

16. Telegram Location handler
17. Haversine
18. Campus radius validation

### Phase 5 — Attendance

19. `/absen`
20. Save attendance
21. Duplicate prevention
22. `/status`

### Phase 6 — CLI

23. User management
24. Attendance management
25. System information

### Phase 7 — Quality

26. Logging
27. Error handling
28. Unit tests
29. README
30. Final verification

Setelah setiap phase selesai, jalankan test dan pastikan fitur sebelumnya tetap bekerja.

---

# 27. Important Design Constraint

Jangan menambahkan fitur yang belum diminta seperti:

* Face recognition
* QR code
* Google Maps API
* Web dashboard
* REST API
* Mobile application
* Email authentication
* OAuth
* AI

Fokus pada MVP:

```text
Telegram
+
NIM/password
+
Telegram User ID
+
GPS Location
+
Geofencing
+
SQLite
+
CLI
```

Jika menemukan keputusan desain yang ambigu, pilih solusi paling sederhana yang sesuai dengan requirement dan jelaskan keputusan tersebut di README.

Sebelum menganggap project selesai, jalankan test suite dan lakukan smoke test terhadap Telegram Bot.
