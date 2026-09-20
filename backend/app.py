from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_connection
from datetime import date

app = Flask(__name__)
CORS(app)  # biar frontend (file HTML terpisah) boleh manggil API ini


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
def update_buku(id_buku):
    body = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE buku SET judul=%s, penulis=%s, stok=%s WHERE id_buku=%s",
        (body["judul"], body["penulis"], body["stok"], id_buku)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Buku diperbarui"})


@app.route("/api/buku/<int:id_buku>", methods=["DELETE"])
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
def get_kategori():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM kategori")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route("/api/anggota", methods=["GET"])
def get_anggota():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM anggota")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route("/api/anggota", methods=["POST"])
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
def get_peminjaman():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id_peminjaman, p.tanggal_peminjaman, p.tanggal_kembali,
               b.judul, a.nama_anggota
        FROM peminjaman p
        JOIN buku b ON p.id_buku = b.id_buku
        JOIN anggota a ON p.id_anggota = a.id_anggota
        ORDER BY p.id_peminjaman DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    # tanggal_kembali null -> masih dipinjam
    # tanggal dari MySQL berupa objek date, diubah ke string biar bisa di-JSON-kan
    for row in data:
        row["status"] = "Dikembalikan" if row["tanggal_kembali"] else "Dipinjam"
        row["tanggal_peminjaman"] = str(row["tanggal_peminjaman"])
        row["tanggal_kembali"] = str(row["tanggal_kembali"]) if row["tanggal_kembali"] else None
    return jsonify(data)

@app.route("/api/peminjaman", methods=["POST"])
def pinjam_buku():
    body = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()

    # Cek stok dulu sebelum kasih pinjam
    cursor.execute("SELECT stok FROM buku WHERE id_buku=%s", (body["id_buku"],))
    row = cursor.fetchone()
    if not row or row[0] <= 0:
        cursor.close()
        conn.close()
        return jsonify({"error": "Stok buku habis"}), 400

    cursor.execute(
        "INSERT INTO peminjaman (id_buku, id_anggota, tanggal_peminjaman) VALUES (%s, %s, %s)",
        (body["id_buku"], body["id_anggota"], date.today())
    )
    cursor.execute("UPDATE buku SET stok = stok - 1 WHERE id_buku=%s", (body["id_buku"],))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Buku berhasil dipinjam"}), 201


@app.route("/api/peminjaman/<int:id_peminjaman>/kembali", methods=["PUT"])
def kembalikan_buku(id_peminjaman):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id_buku FROM peminjaman WHERE id_peminjaman=%s", (id_peminjaman,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Data peminjaman tidak ditemukan"}), 404

    cursor.execute(
        "UPDATE peminjaman SET tanggal_kembali=%s WHERE id_peminjaman=%s",
        (date.today(), id_peminjaman)
    )
    cursor.execute("UPDATE buku SET stok = stok + 1 WHERE id_buku=%s", (row[0],))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Buku dikembalikan"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
