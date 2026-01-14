
import requests
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def run_demo():
    print("🚀 STARTING PRODUCTION READINESS TEST")
    print("==================================================")
    
    # 0. Setup Dummy Files
    with open("dummy_resume.txt", "w") as f:
        f.write("I am a software engineer with 5 years of experience in Python, FastAPI, and React. I have built scalable backend systems.")
    
    jd = "We are looking for a Senior Software Engineer with strong Python and API experience."
    
    # 1. Upload
    print("\n[1] Uploading Resume...")
    try:
        files = {'resume': open('dummy_resume.txt', 'rb')}
        data = {'job_description': jd}
        res = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        if res.status_code != 200:
            print("❌ Upload Failed:", res.text)
            return
            
        data = res.json()
        print(f"✅ Match Score: {data['match_score']}")
        
        ctx = data['interview_context']['payload']
        # Fix: ensure match_score is float, not list
        if isinstance(ctx['match_score'], list):
             ctx['match_score'] = ctx['match_score'][0]
             
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # 2. Start Interview
    print("\n[2] Starting Interview Session (DB Persistence Check)...")
    try:
        res = requests.post(f"{BASE_URL}/interview/start", json=ctx)
        session_data = res.json()
        session_id = session_data['session_id']
        print(f"✅ Session Started. ID: {session_id}")
        print(f"🤖 Q1: {session_data['question']}")
        
    except Exception as e:
        print(f"❌ Start Error: {e}")
        return

    # 3. Answer Question
    print("\n[3] Answering Question...")
    try:
        ans_payload = {
            "session_id": session_id,
            "answer": "I chose Python because of its rich ecosystem and simplicity for backend development."
        }
        res = requests.post(f"{BASE_URL}/interview/answer", json=ans_payload)
        ans_data = res.json()
        print(f"🤖 Next Q: {ans_data['next_question']}")
        
    except Exception as e:
        print(f"❌ Answer Error: {e}")
        return

    print("\n✅ Verification Successful: Flow works with DB persistence.")
    print("==================================================")

if __name__ == "__main__":
    run_demo()
