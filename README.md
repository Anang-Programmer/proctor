# 🎓 Sistem Ujian Online dengan Proctor Otomatis

Sistem ujian online yang dilengkapi dengan teknologi **Proctor Otomatis** menggunakan Computer Vision untuk mencegah kecurangan selama ujian berlangsung.

## ✨ Fitur Utama

### 🔒 Sistem Proctor Otomatis
- **Deteksi Pose**: Monitoring posisi bahu dan kepala siswa
- **Deteksi Wajah**: Memastikan hanya satu wajah yang terdeteksi
- **Deteksi Objek**: Mendeteksi benda terlarang (HP, laptop, buku)
- **Screenshot Otomatis**: Bukti pelanggaran tersimpan otomatis
- **Sistem Peringatan Bertingkat**: 3 kali pelanggaran = ujian berakhir

### 👨‍💼 Panel Admin
- ✅ Kelola bank soal (CRUD)
- ✅ Buat dan atur ujian
- ✅ Manajemen peserta ujian
- ✅ Lihat hasil ujian dan statistik
- ✅ Monitor log pelanggaran dengan bukti screenshot

### 👨‍🎓 Panel Siswa
- ✅ Dashboard ujian tersedia
- ✅ Interface ujian dengan proctor aktif
- ✅ Timer ujian real-time
- ✅ Navigasi soal yang mudah
- ✅ Riwayat ujian dan nilai

## 🛠️ Teknologi yang Digunakan

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Database**: MySQL
- **Computer Vision**: OpenCV, MediaPipe, YOLO v8
- **Authentication**: Flask-Login
- **Real-time**: WebSocket untuk monitoring

## 📋 Persyaratan Sistem

- Python 3.8+
- MySQL Server
- Webcam/Camera
- Browser modern (Chrome, Firefox, Edge)

## 🚀 Instalasi

### 1. Clone Repository
```bash
git clone <repository-url>
cd sistem-ujian-proctor
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Database
```bash
# Pastikan MySQL server berjalan
python create_database.py
```

### 4. Konfigurasi Database
Edit file `app.py` pada bagian database configuration:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/ujian_proctor'
```

### 5. Jalankan Aplikasi
```bash
python app.py
```

Aplikasi akan berjalan di `http://localhost:5000`

## 👤 Akun Demo

### Admin
- **Username**: `admin`
- **Password**: `admin123`

### Siswa
- **Username**: `siswa1`
- **Password**: `siswa123`

## 📖 Cara Penggunaan

### Untuk Admin:
1. Login dengan akun admin
2. Kelola bank soal di menu "Kelola Bank Soal"
3. Buat ujian baru di menu "Kelola Ujian"
4. Monitor hasil ujian dan pelanggaran

### Untuk Siswa:
1. Login dengan akun siswa
2. Pilih ujian yang tersedia
3. Klik "Mulai Ujian" dan ikuti instruksi
4. Pastikan kamera berfungsi dan pencahayaan cukup
5. Kerjakan ujian dengan tenang

## ⚠️ Aturan Ujian

### Pelanggaran Ringan:
- Bahu tidak terlihat jelas
- Kepala terlalu sering menengok
- Wajah tidak terdeteksi sementara

### Pelanggaran Berat:
- Terdeteksi handphone/laptop/buku
- Wajah orang lain terdeteksi
- Keluar dari fullscreen
- Mencoba membuka developer tools

### Konsekuensi:
- **1-2 Pelanggaran**: Peringatan pop-up
- **3 Pelanggaran**: Ujian dihentikan otomatis

## 📁 Struktur Project

```
sistem-ujian-proctor/
├── app.py                 # Main Flask application
├── proctor_system.py      # Proctor monitoring system
├── create_database.py     # Database setup script
├── requirements.txt       # Python dependencies
├── main.py               # Original proctor model
├── yolov8n.pt           # YOLO model file
├── templates/           # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── admin/          # Admin templates
│   └── siswa/          # Student templates
├── static/             # Static files
│   ├── css/
│   ├── js/
│   └── screenshots/    # Violation screenshots
└── README.md
```

## 🔧 Konfigurasi

### Database Configuration
```python
# app.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:pass@localhost/ujian_proctor'
```

### Proctor Settings
```python
# proctor_system.py
self.max_pelanggaran = 3  # Maximum violations
self.cooldown = 3         # Cooldown between warnings (seconds)
```

## 🐛 Troubleshooting

### Kamera tidak terdeteksi
- Pastikan webcam terhubung dan tidak digunakan aplikasi lain
- Berikan permission camera ke browser
- Restart browser jika perlu

### Database connection error
- Pastikan MySQL server berjalan
- Periksa username/password database
- Pastikan database `ujian_proctor` sudah dibuat

### YOLO model error
- Pastikan file `yolov8n.pt` ada di root directory
- Install ultralytics: `pip install ultralytics`

## 📈 Pengembangan Selanjutnya

- [ ] Live monitoring dashboard untuk admin
- [ ] Export hasil ujian ke PDF/Excel
- [ ] Integrasi dengan LMS (Learning Management System)
- [ ] Mobile app untuk siswa
- [ ] Advanced analytics dan reporting
- [ ] Multi-language support

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan:
1. Fork repository ini
2. Buat branch fitur baru
3. Commit perubahan Anda
4. Push ke branch
5. Buat Pull Request

## 📄 Lisensi

Project ini menggunakan lisensi MIT. Lihat file `LICENSE` untuk detail.

## 📞 Support

Jika mengalami masalah atau butuh bantuan:
- Buat issue di GitHub repository
- Email: support@ujian-proctor.com

---

**Dibuat dengan ❤️ untuk pendidikan yang lebih baik dan fair**