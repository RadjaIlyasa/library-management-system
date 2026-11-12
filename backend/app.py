from flask import Flask, jsonify, request, g
from itsdangerous import URLSafeTimedSerializer
from itsdangerous import BadSignature, SignatureExpired
from flask_cors import CORS
from db import get_connection
from datetime import date
from functools import wraps
from werkzeug.security import check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Ambil daftar frontend yang diizinkan dari .env
frontend_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500"
    ).split(",")
    if origin.strip()
]

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": frontend_origins
        }
    },
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)


# =====================================
# KONFIGURASI TOKEN AUTENTIKASI
# =====================================

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY belum dikonfigurasi!")

token_serializer = URLSafeTimedSerializer(
    app.config["SECRET_KEY"],
    salt="perpustakaan-admin-auth"
)

TOKEN_MAX_AGE = int(
    os.getenv("TOKEN_MAX_AGE_SECONDS", "3600")
)


# =====================================
# DECORATOR LOGIN REQUIRED
# =====================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split(" ", 1)

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "error": "Token autentikasi tidak ditemukan"
            }), 401

        token = parts[1].strip()

        try:
            payload = token_serializer.loads(
                token,
                max_age=TOKEN_MAX_AGE
            )

            admin_id = int(payload["admin_id"])
            token_version = int(payload["token_version"])

        except SignatureExpired:
            return jsonify({
                "error": "Token kedaluwarsa, silakan login kembali"
            }), 401

        except (BadSignature, KeyError, TypeError, ValueError):
            return jsonify({
                "error": "Token tidak valid"
            }), 401

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT token_version FROM admin WHERE id_admin=%s",
                (admin_id,)
            )

            admin = cursor.fetchone()

        finally:
            cursor.close()
            conn.close()

        if not admin or admin["token_version"] != token_version:
            return jsonify({
                "error": "Sesi sudah tidak berlaku, silakan login kembali"
            }), 401

        g.admin = payload

        return f(*args, **kwargs)

    return decorated


@app.route("/api/login", methods=["POST"])

@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}

    username = (body.get("username") or "").strip()
    password = body.get("password") or ""

    if not username or not password:
        return jsonify({
            "error": "Username dan password wajib diisi"
        }), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id_admin, username, password_hash, token_version
            FROM admin
            WHERE username=%s
            """,
            (username,)
        )

        admin = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if not admin or not check_password_hash(
        admin["password_hash"], password
    ):
        return jsonify({
            "error": "Username atau password salah"
        }), 401

    token = token_serializer.dumps({
        "admin_id": admin["id_admin"],
        "username": admin["username"],
        "token_version": admin["token_version"]
    })

    return jsonify({
        "token": token,
        "expires_in": TOKEN_MAX_AGE
    })




@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE admin
            SET token_version = token_version + 1
            WHERE id_admin = %s
            AND token_version = %s
            """,
            (
                g.admin["admin_id"],
                g.admin["token_version"]
            )
        )

        if cursor.rowcount != 1:
            conn.rollback()
            return jsonify({
                "error": "Sesi sudah tidak berlaku"
            }), 401

        conn.commit()

        return jsonify({
            "message": "Logout berhasil"
        })

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

# ---------- BUKU ----------

@app.route("/api/buku", methods=["GET"])
def get_buku():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.id_buku, b.judul, b.penulis, b.stok, k.nama_kategori
        FROM buku b
        LEFT JOIN kategori k ON b.id_kategori = k.id_kategori
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route("/api/buku", methods=["POST"])
@login_required
def tambah_buku():
    body = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    # Query parameterized -> aman dari SQL injection
    cursor.execute(
        "INSERT INTO buku (judul, penulis, id_kategori, stok) VALUES (%s, %s, %s, %s)",
        (body["judul"], body["penulis"], body.get("id_kategori"), body.get("stok", 0))
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Buku ditambahkan", "id_buku": new_id}), 201



@app.route("/api/buku/<int:id_buku>", methods=["PUT"])
@login_required
def update_buku(id_buku):
    body = request.get_json()

    conn = get_connection()
    cursor = conn.cursor()

    id_kategori = body.get("id_kategori")

    if id_kategori == "":
        id_kategori = None

    cursor.execute(
        """
        UPDATE buku
        SET judul=%s, penulis=%s, id_kategori=%s, stok=%s
        WHERE id_buku=%s
        """,
        (
            body["judul"],
            body["penulis"],
            id_kategori,
            body["stok"],
            id_buku
        )
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Buku diperbarui"})


@app.route("/api/buku/<int:id_buku>", methods=["DELETE"])
@login_required
def hapus_buku(id_buku):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM buku WHERE id_buku=%s", (id_buku,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Buku dihapus"})


# ---------- KATEGORI & ANGGOTA (buat dropdown di frontend) ----------

@app.route("/api/kategori", methods=["GET"])
@login_required
def get_kategori():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM kategori")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route("/api/anggota", methods=["GET"])
@login_required
def get_anggota():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM anggota")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route("/api/anggota", methods=["POST"])
@login_required
def tambah_anggota():
    body = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    # Kolom disesuaikan dengan tabel anggota kamu: nama_anggota, alamat, no_hp
    cursor.execute(
        "INSERT INTO anggota (nama_anggota, alamat, no_hp) VALUES (%s, %s, %s)",
        (body["nama_anggota"], body.get("alamat"), body.get("no_hp"))
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Anggota ditambahkan", "id_anggota": new_id}), 201


# ---------- PEMINJAMAN ----------


@app.route("/api/peminjaman", methods=["GET"])
@login_required
def get_peminjaman():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT p.id_peminjaman,
                   p.tanggal_peminjaman,
                   p.tanggal_kembali,
                   p.status,
                   b.judul,
                   a.nama_anggota
            FROM peminjaman p
            JOIN buku b ON p.id_buku = b.id_buku
            JOIN anggota a ON p.id_anggota = a.id_anggota
            ORDER BY p.id_peminjaman DESC
        """)

        data = cursor.fetchall()

        label_status = {
            "dipinjam": "Dipinjam",
            "dikembalikan": "Dikembalikan",
            "terlambat": "Terlambat"
        }

        for row in data:
            row["status"] = label_status.get(
                row["status"], row["status"]
            )
            row["tanggal_peminjaman"] = str(
                row["tanggal_peminjaman"]
            )
            row["tanggal_kembali"] = (
                str(row["tanggal_kembali"])
                if row["tanggal_kembali"]
                else None
            )

        return jsonify(data)

    finally:
        cursor.close()
        conn.close()


@app.route("/api/peminjaman/anggota/<int:id_anggota>", methods=["GET"])
@login_required
def get_riwayat_anggota(id_anggota):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT p.id_peminjaman,
                   p.tanggal_peminjaman,
                   p.tanggal_kembali,
                   p.status,
                   b.judul
            FROM peminjaman p
            JOIN buku b ON p.id_buku = b.id_buku
            WHERE p.id_anggota = %s
            ORDER BY p.id_peminjaman DESC
        """, (id_anggota,))

        data = cursor.fetchall()

        label_status = {
            "dipinjam": "Dipinjam",
            "dikembalikan": "Dikembalikan",
            "terlambat": "Terlambat"
        }

        for row in data:
            row["status"] = label_status.get(
                row["status"], row["status"]
            )
            row["tanggal_peminjaman"] = str(
                row["tanggal_peminjaman"]
            )
            row["tanggal_kembali"] = (
                str(row["tanggal_kembali"])
                if row["tanggal_kembali"]
                else None
            )

        return jsonify(data)

    finally:
        cursor.close()
        conn.close()



@app.route("/api/peminjaman", methods=["POST"])
@login_required
def pinjam_buku():
    body = request.get_json()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        conn.start_transaction()

        # Kunci baris buku selama transaksi berlangsung
        cursor.execute(
            "SELECT stok FROM buku WHERE id_buku=%s FOR UPDATE",
            (body["id_buku"],)
        )

        row = cursor.fetchone()

        if not row or row[0] <= 0:
            conn.rollback()
            return jsonify({"error": "Stok buku habis"}), 400

        cursor.execute(
            """
            INSERT INTO peminjaman
            (id_buku, id_anggota, tanggal_peminjaman, status)
            VALUES (%s, %s, %s, 'dipinjam')
            """,
            (
                body["id_buku"],
                body["id_anggota"],
                date.today()
            )
        )

        cursor.execute(
            "UPDATE buku SET stok = stok - 1 WHERE id_buku=%s",
            (body["id_buku"],)
        )

        conn.commit()

        return jsonify({
            "message": "Buku berhasil dipinjam"
        }), 201

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()




@app.route("/api/peminjaman/<int:id_peminjaman>/kembali", methods=["PUT"])
@login_required
def kembalikan_buku(id_peminjaman):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        # Kunci transaksi peminjaman agar tidak diproses bersamaan
        cursor.execute(
            """
            SELECT id_buku, tanggal_kembali
            FROM peminjaman
            WHERE id_peminjaman=%s
            FOR UPDATE
            """,
            (id_peminjaman,)
        )

        row = cursor.fetchone()

        if not row:
            conn.rollback()
            return jsonify({
                "error": "Data peminjaman tidak ditemukan"
            }), 404

        if row["tanggal_kembali"] is not None:
            conn.rollback()
            return jsonify({
                "error": "Buku sudah pernah dikembalikan"
            }), 409

        cursor.execute(
            """
            UPDATE peminjaman
            SET tanggal_kembali=%s,
                status='dikembalikan'
            WHERE id_peminjaman=%s
            AND tanggal_kembali IS NULL
            """,
            (date.today(), id_peminjaman)
        )

        if cursor.rowcount != 1:
            conn.rollback()
            return jsonify({
                "error": "Pengembalian gagal diproses"
            }), 409

        cursor.execute(
            "UPDATE buku SET stok = stok + 1 WHERE id_buku=%s",
            (row["id_buku"],)
        )

        conn.commit()

        return jsonify({
            "message": "Buku berhasil dikembalikan"
        })

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()



if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=debug_mode
    )