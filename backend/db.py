
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# Lokasi folder backend
BASE_DIR = Path(__file__).resolve().parent

# Membaca konfigurasi dari backend/.env
load_dotenv(BASE_DIR / ".env")


def get_connection():
    ssl_ca = os.getenv("DB_SSL_CA")

    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "perpustakaan"),
        "connection_timeout": 15,
    }

    # Konfigurasi TLS untuk TiDB Cloud
    if ssl_ca:
        cert_path = Path(ssl_ca)

        if not cert_path.is_absolute():
            cert_path = BASE_DIR / cert_path

        cert_path = cert_path.resolve()

        if not cert_path.is_file():
            raise FileNotFoundError(
                f"CA Certificate tidak ditemukan: {cert_path}"
            )

        config.update({
            "ssl_ca": str(cert_path),
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
        })

    return mysql.connector.connect(**config)
