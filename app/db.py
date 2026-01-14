import sqlite3
import uuid
import os
import json
from typing import List, Optional, Dict

# ✅ absolute path (Windows safe)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DATA_DIR, "candidates.db")

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)  # 🔥 folder auto-create
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            name TEXT,
            resume_text TEXT,
            job_description TEXT,
            match_score REAL,
            interview_score REAL,
            final_score REAL,
            status TEXT,
            feedback_data TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_candidate(name: str, resume_text: str, jd: str, match_score: float) -> str:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    cid = str(uuid.uuid4())
    c.execute("""
        INSERT INTO candidates
        (id, name, resume_text, job_description, match_score, interview_score, final_score, status, feedback_data)
        VALUES (?, ?, ?, ?, ?, 0, 0, 'Matched', '{}')
    """, (cid, name, resume_text, jd, match_score))
    conn.commit()
    conn.close()
    return cid

def get_leaderboard() -> List[Dict]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM candidates ORDER BY match_score DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_candidate(cid: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM candidates WHERE id = ?", (cid,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def update_candidate_interview(cid: str, interview_score: float, final_score: float, feedback: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        UPDATE candidates
        SET interview_score = ?, final_score = ?, status = 'Interviewed', feedback_data = ?
        WHERE id = ?
    """, (interview_score, final_score, json.dumps(feedback), cid))
    conn.commit()
    conn.close()

def clear_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM candidates")
    conn.commit()
    conn.close()
