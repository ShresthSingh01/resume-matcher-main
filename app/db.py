import sqlite3
import uuid
import os
import json
from typing import List, Optional, Dict

DB_FILE = "data/valid_candidates.db"

def init_db():
    try:
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
                feedback_data TEXT,
                status TEXT,
                feedback_data TEXT,
                matched_skills TEXT,
                missing_skills TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS interview_sessions (
                session_id TEXT PRIMARY KEY,
                candidate_id TEXT,
                role TEXT,
                current_question TEXT,
                scores TEXT, -- JSON list of scores
                is_active BOOLEAN,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS interview_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT, -- user, assistant
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES interview_sessions(session_id)
            )
        ''')
        # Schema Migration: Ensure new columns exist for existing DBs
        try:
            c.execute("ALTER TABLE candidates ADD COLUMN matched_skills TEXT")
        except: pass
        
        try:
            c.execute("ALTER TABLE candidates ADD COLUMN missing_skills TEXT")
        except: pass
        
        try:
            c.execute("ALTER TABLE candidates ADD COLUMN resume_evaluation_data TEXT")
        except: pass
        
        try:
            c.execute("ALTER TABLE candidates ADD COLUMN flags TEXT")
        except: pass

        conn.commit()
        conn.close()
        print(f"✅ Database initialized at {DB_FILE}")
    except Exception as e:
        print(f"❌ Database Init Error: {e}")


def get_conn():
    return sqlite3.connect(DB_FILE)

def add_candidate(name: str, resume_text: str, jd: str, match_score: float, matched_skills: list, missing_skills: list, resume_evaluation: dict = {}, status: str = "Matched") -> str:
    conn = get_conn()
    c = conn.cursor()
    cid = str(uuid.uuid4())
    c.execute("""
        INSERT INTO candidates
        (id, name, resume_text, job_description, match_score, interview_score, final_score, status, feedback_data, matched_skills, missing_skills, resume_evaluation_data)
        VALUES (?, ?, ?, ?, ?, 0, 0, ?, '{}', ?, ?, ?)
    """, (cid, name, resume_text, jd, match_score, status, json.dumps(matched_skills), json.dumps(missing_skills), json.dumps(resume_evaluation)))
    conn.commit()
    conn.close()
    return cid

def get_leaderboard() -> List[Dict]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM candidates ORDER BY final_score DESC, match_score DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
    return [dict(row) for row in rows]

def get_candidate(cid: str) -> Optional[Dict]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM candidates WHERE id = ?', (cid,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_candidate_interview(cid: str, interview_score: float, final_score: float, feedback: dict, status: str = 'completed'):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        UPDATE candidates 
        SET interview_score = ?, final_score = ?, status = ?, feedback_data = ?
        WHERE id = ?
    ''', (interview_score, final_score, status, json.dumps(feedback), cid))
    conn.commit()
    conn.close()
    return True

def flag_candidate(cid: str, violation: str):
    conn = get_conn()
    c = conn.cursor()
    # Get existing flags
    c.execute("SELECT flags FROM candidates WHERE id = ?", (cid,))
    row = c.fetchone()
    current_flags = []
    if row and row[0]:
        try:
            current_flags = json.loads(row[0])
        except: pass
    
    current_flags.append({"violation": violation, "timestamp": str(uuid.uuid4())}) # simplified tsp
    
    c.execute("UPDATE candidates SET flags = ? WHERE id = ?", (json.dumps(current_flags), cid))
    conn.commit()
    conn.close()

def update_candidate_status(cid: str, status: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE candidates SET status = ? WHERE id = ?", (status, cid))
    conn.commit()
    conn.close()

# --- New Session Functions ---

def save_session_db(session_id: str, candidate_id: str, role: str, is_active: bool = True):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR REPLACE INTO interview_sessions (session_id, candidate_id, role, current_question, scores, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, candidate_id, role, "", "[]", is_active))
        conn.commit()
    except Exception as e:
        print(f"DB Error save_session: {e}")
    finally:
        conn.close()

def get_session_db(session_id: str):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM interview_sessions WHERE session_id=?", (session_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_session_db(session_id: str, current_question: str, scores: list, is_active: bool):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE interview_sessions 
            SET current_question = ?, scores = ?, is_active = ?
            WHERE session_id = ?
        ''', (current_question, json.dumps(scores), is_active, session_id))
        conn.commit()
    except Exception as e:
        print(f"DB Error update_session: {e}")
    finally:
        conn.close()

def log_message_db(session_id: str, role: str, content: str):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO interview_messages (session_id, role, content)
            VALUES (?, ?, ?)
        ''', (session_id, role, content))
        conn.commit()
    except Exception as e:
        print(f"DB Error log_message: {e}")
    finally:
        conn.close()

def get_session_messages(session_id: str):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM interview_messages WHERE session_id=? ORDER BY timestamp ASC", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM candidates')
    c.execute('DELETE FROM interview_sessions')
    c.execute('DELETE FROM interview_messages')
    conn.commit()
    conn.close()

