import mysql.connector

def get_connection():
    # Ganti sesuai konfigurasi MySQL Workbench-mu
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="perpustakaan"
    )
