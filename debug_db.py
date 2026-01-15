
import sqlite3
import json

DB_FILE = "data/valid_candidates.db"

def check_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Check Table Info
        print("--- Table Info: candidates ---")
        c.execute("PRAGMA table_info(candidates)")
        columns = c.fetchall()
        for col in columns:
            print(col)
            
        # Check Data
        print("\n--- Data Sample ---")
        c.execute("SELECT * FROM candidates LIMIT 1")
        row = c.fetchone()
        print(row)
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
