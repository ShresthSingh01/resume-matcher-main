import urllib.request
import urllib.error
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def post_json(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise
    except Exception as e:
        print(f"Error calling {url}: {e}")
        raise

def test_interview_flow():
    print("1. Starting Interview...")
    start_payload = {
        "resume_text": "Experienced Python Developer with Flask and Django skills. Strong SQL knowledge.",
        "job_description": "We are looking for a Senior Python Engineer. Must be expert in Python, API design, and Database optimization.",
        "match_score": 85.0
    }
    
    try:
        data = post_json("/interview/start", start_payload)
        print(f"✅ Session Started: {data['session_id']}")
        print(f"   Detected Role: {data['role']}")
        print(f"   Q1: {data['question']}")
        
        session_id = data['session_id']
        
        # 2. Answer Q1
        print("\n2. Answering Q1...")
        answer_payload = {
            "session_id": session_id,
            "answer": "To optimize database queries, I use indexing and avoid N+1 problems by using select_related in Django."
        }
        data = post_json("/interview/answer", answer_payload)
        print(f"✅ Answer recorded.")
        print(f"   Next Question: {data.get('next_question')}")
        
        # 3. Get Results (Mid-way check)
        print("\n3. Checking result endpoint...")
        data = post_json("/interview/result", {"session_id": session_id})
        print("✅ Result fetched successfully:")
        print(json.dumps(data, indent=2))
        
        print("\n🎉 ALL TESTS PASSED!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")

if __name__ == "__main__":
    test_interview_flow()
