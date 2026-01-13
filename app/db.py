import sqlite3
import uuid
from typing import List, Optional, Dict
import json

DB_FILE = "data/candidates.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
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
    ''')
    conn.commit()
    conn.close()

def add_candidate(name: str, resume_text: str, jd: str, match_score: float) -> str:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    cid = str(uuid.uuid4())
    c.execute('''
        INSERT INTO candidates (id, name, resume_text, job_description, match_score, interview_score, final_score, status, feedback_data)
        VALUES (?, ?, ?, ?, ?, 0, 0, 'Matched', '{}')
    ''', (cid, name, resume_text, jd, match_score))
    conn.commit()
    conn.close()
    return cid

def get_leaderboard() -> List[Dict]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM candidates ORDER BY match_score DESC')
    rows = c.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append(dict(row))
    return results

def get_candidate(cid: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM candidates WHERE id = ?', (cid,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_candidate_interview(cid: str, interview_score: float, final_score: float, feedback: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE candidates 
        SET interview_score = ?, final_score = ?, status = 'Interviewed', feedback_data = ?
        WHERE id = ?
    ''', (interview_score, final_score, json.dumps(feedback), cid))
    conn.commit()
    conn.close()

def clear_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM candidates')
    conn.commit()
    conn.close()
