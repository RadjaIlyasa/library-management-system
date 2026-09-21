from werkzeug.security import generate_password_hash
from db import get_connection

username = input("username admin: ")
password = input("password admin: ")

conn = get_connection()
cursor = conn.cursor()
cursor.execute(
    "INSERT INTO admin (username, password_hash) VALUES (%s, %s)",
    (username, generate_password_hash(password))
)
conn.commit()
cursor.close()
conn.close()
print("Admin berhasil dibuat.")
