import urllib.request
import urllib.parse
import json
import uuid

BASE_URL = "http://localhost:8000"

def post_json(url, data):
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode('utf-8'))

def upload_resume():
    # Constructing multipart/form-data manually with urllib is painful.
    # I'll rely on the existing candidates if any, or skip upload and try to interview an existing one?
    # No, I need a candidate ID.
    # Let's try to use minimal multipart construction.
    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
    
    body = []
    # Resume File
    body.append(f'--{boundary}')
    body.append('Content-Disposition: form-data; name="resumes"; filename="dummy.txt"')
    body.append('Content-Type: text/plain')
    body.append('')
    body.append('Name: Test Candidate\nEmail: test@example.com\nSkills: Python, AI')
    
    # JD
    body.append(f'--{boundary}')
    body.append('Content-Disposition: form-data; name="job_description"')
    body.append('')
    body.append('Looking for Python AI Engineer.')
    
    body.append(f'--{boundary}--')
    body.append('')
    
    body_bytes = '\r\n'.join(body).encode('utf-8')
    
    req = urllib.request.Request(
        f"{BASE_URL}/upload",
        data=body_bytes,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': len(body_bytes)
        }
    )
    
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode('utf-8'))

def test_flow():
    print("🚀 Starting Batch Flow Verification (urllib)...")

    # 1. Upload Resume
    print("\n1️⃣ Uploading Resume...")
    try:
        candidates = upload_resume()
        print(f"✅ Upload Success. Candidates: {len(candidates)}")
        cid = candidates[0]['candidate_id']
        print(f"🆔 Candidate ID: {cid}")
    except Exception as e:
        print(f"❌ Upload Failed: {e}")
        return

    # 2. Start Interview by ID
    print(f"\n2️⃣ Starting Interview for {cid}...")
    try:
        session = post_json(f"{BASE_URL}/interview/start", {'candidate_id': cid})
        sid = session['session_id']
        print(f"✅ Session Started. ID: {sid}")
        print(f"🤖 Question: {session['question']}")
    except Exception as e:
        print(f"❌ Start Failed: {e}")
        return

    # 3. Answer Questions (simulate loop)
    print("\n3️⃣ Simulating Answers...")
    for i in range(5):
        answer = "I have experience with Python and building AI agents."
        try:
            data = post_json(f"{BASE_URL}/interview/answer", {'session_id': sid, 'answer': answer})
            print(f"   Shape: {data.get('is_finished')}")
            if data.get('is_finished'):
                print("✅ Interview Finished!")
                break
        except Exception as e:
            print(f"❌ Answer Error: {e}")
            break
            
    # 4. Check Result
    print("\n4️⃣ Checking Final Result...")
    try:
        result = post_json(f"{BASE_URL}/interview/result", {'session_id': sid})
        print(f"🏆 Final Score: {result.get('final_score')}")
    except Exception as e:
        print(f"❌ Result Error: {e}")

    # 5. Check Leaderboard
    print("\n5️⃣ Checking Leaderboard...")
    try:
        with urllib.request.urlopen(f"{BASE_URL}/leaderboard") as res:
            lb = json.loads(res.read().decode('utf-8'))
            top = lb[0]
            if top['id'] == cid:
                print(f"✅ Candidate is #1 on Leaderboard with score {top['final_score']}")
            else:
                print(f"⚠️ Candidate not #1? Top is {top['id']}")
    except Exception as e:
        print(f"❌ Leaderboard Error: {e}")

if __name__ == "__main__":
    test_flow()
