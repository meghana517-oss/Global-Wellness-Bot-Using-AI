import bcrypt
import sqlite3

DB_PATH = "../wellness.db"  # Change path if needed
USERNAME = "admin"
NEW_PASSWORD = "admin123"  # Set your desired password here

# Hash the new password
hashed = bcrypt.hashpw(NEW_PASSWORD.encode(), bcrypt.gensalt()).decode()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Update password for existing admin
cursor.execute("UPDATE admins SET password = ? WHERE username = ?", (hashed, USERNAME))
conn.commit()

# Confirm update
cursor.execute("SELECT username, password FROM admins WHERE username = ?", (USERNAME,))
row = cursor.fetchone()
print(f"Updated admin: {row}")

conn.close()
print("Admin password reset complete. Use username 'admin' and password 'admin123' to login.")
