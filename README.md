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

## Alur belajar yang bisa kamu eksplor selanjutnya
1. ~~Edit buku~~ ✅ dan ~~Peminjaman~~ ✅ sudah ada.
2. **Tambah autentikasi**: login admin sebelum bisa tambah/hapus/edit buku (belajar hashing password & session/JWT). Ini prioritas paling penting berikutnya.
3. **Validasi & error handling** yang lebih rapi di sisi frontend (sekarang masih minim, misalnya belum ada pengecekan format no HP).
4. **Riwayat keterlambatan**: hitung selisih hari dari `tanggal_pinjam` ke hari ini untuk peminjaman yang belum dikembalikan.
5. Kalau udah pede, migrasi frontend dari vanilla JS ke Next.js — struktur API-nya udah reusable karena berbasis REST.
