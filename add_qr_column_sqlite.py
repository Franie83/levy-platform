# add_qr_column_sqlite.py
import sqlite3
import os

def add_qr_column_to_sqlite():
    """Add qr_code column to SQLite database"""
    db_path = 'levy_platform.db'  # or your database path
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'qr_code' not in columns:
        print("Adding qr_code column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN qr_code VARCHAR(200)")
        conn.commit()
        print("✅ qr_code column added successfully")
    else:
        print("✅ qr_code column already exists")
    
    conn.close()

if __name__ == "__main__":
    add_qr_column_to_sqlite()