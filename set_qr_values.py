# set_qr_values.py
import sqlite3

conn = sqlite3.connect('instance/levy_platform.db')
cursor = conn.cursor()

# Check current QR codes
cursor.execute("SELECT id, name, nin, qr_code FROM users WHERE role='payee'")
rows = cursor.fetchall()
print("Current payee users:")
for row in rows:
    print(f"  ID: {row[0]}, Name: {row[1]}, NIN: {row[2]}, QR Code: {row[3]}")

# Update MSME user (id=3)
cursor.execute("UPDATE users SET qr_code = 'user_qr_3_00000000003.png' WHERE id = 3")
# Update Transporter user (id=4)
cursor.execute("UPDATE users SET qr_code = 'user_qr_4_00000000004.png' WHERE id = 4")

conn.commit()

# Verify the update
cursor.execute("SELECT id, name, nin, qr_code FROM users WHERE role='payee'")
rows = cursor.fetchall()
print("\nUpdated payee users:")
for row in rows:
    print(f"  ID: {row[0]}, Name: {row[1]}, NIN: {row[2]}, QR Code: {row[3]}")

conn.close()
print("\n✅ QR codes set in database!")