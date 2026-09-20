# Sistem Perpustakaan — Flask + MySQL + HTML/CSS/JS

## 1. Setup database
- Buka MySQL Workbench, jalankan isi file `backend/schema.sql`.
- Ini akan bikin database `perpustakaan` + tabel + data contoh.

## 2. Setup backend (Flask)
```bash
cd backend
pip install -r requirements.txt
```
- Edit `db.py`, ganti `ISI_PASSWORD_MYSQL_KAMU` dengan password MySQL-mu.
```bash
python app.py
```
- API akan jalan di `http://localhost:5000`

## 3. Jalankan frontend
- Buka `frontend/index.html` langsung di browser (double click),
  atau pakai Live Server extension di VS Code.

## Catatan skema anggota
Endpoint `/api/anggota` (POST) dan tampilan tabel anggota mengikuti kolom `nama_anggota`, `alamat`, `no_hp` — sesuaikan lagi kalau struktur tabel `anggota` di database kamu berbeda.
