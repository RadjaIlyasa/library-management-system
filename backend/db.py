
import os
import mysql.connector
from dotenv import load_dotenv

# Membaca konfigurasi dari file .env saat development
# Di hosting, konfigurasi akan berasal dari environment variables
load_dotenv()


def get_connection():
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "perpustakaan"),
        "connection_timeout": 10,
    }

    # SSL digunakan apabila database cloud membutuhkannya
    ssl_ca = os.getenv("DB_SSL_CA")

    if ssl_ca:
        config["ssl_ca"] = ssl_ca
        config["ssl_verify_cert"] = True

    return mysql.connector.connect(**config)
