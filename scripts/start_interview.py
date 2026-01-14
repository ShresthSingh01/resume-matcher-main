import requests
import os
import sys

BASE_URL = "http://127.0.0.1:8000"
RESUME_FILE = "resume.pdf" # Default file to look for
JD_FILE = "jd.txt"

def print_header(title):
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def step_match_resume():
    print_header("STEP 1: RESUME MATCHING")
    
    # Check for files
    r_file = RESUME_FILE
    j_file = JD_FILE
    
    if len(sys.argv) > 1:
        r_file = sys.argv[1]
    if len(sys.argv) > 2:
        j_file = sys.argv[2]

    if not os.path.exists(r_file):
        print(f"❌ Error: File {r_file} not found.")
        print("Usage: python start_interview.py [resume.pdf] [jd.txt]")
        sys.exit(1)
        
    print(f"📄 Uploading {r_file}...")
    
    files = {
        "resume": (os.path.basename(r_file), open(r_file, "rb")),
    }
    
    data = {"job_description": ""}
    
    # If JD is a file, upload it. If it's text, we'd need a different handling,
    # but here we assume file for simplicity or read it.
    if os.path.exists(j_file):
        print(f"📄 Uploading {j_file}...")
        files["jd_file"] = (os.path.basename(j_file), open(j_file, "rb"))
    else:
        print("⚠️ JD file not found, using dummy text or prompt input?")
        jd_text = input("Paste Job Description (or press Enter to skip if using defaults): ")
        if jd_text:
            data["job_description"] = jd_text
        else:
             print("❌ JD is required.")
             sys.exit(1)
    
    try:
        response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            sys.exit(1)
            
        data = response.json()
        print("\n✅ Match Complete!")
        print(f"   Match Score: {data['match_score']}/100")
        print(f"   Reasoning: {data.get('reasoning', 'N/A')}")
        
        matched = data.get('matched_skills', [])
        missing = data.get('missing_skills', [])
        
        print(f"   Skills Found: {', '.join(matched[:5])}{'...' if len(matched)>5 else ''}")
        print(f"   Skills Missing: {', '.join(missing[:5])}{'...' if len(missing)>5 else ''}")
        
        return data
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("Make sure server is running: uvicorn app.main:app --reload")
        sys.exit(1)

def step_interview(context_data):
    print_header("STEP 2: AI INTERVIEW")
    
    ctx = context_data.get('interview_context', {})
    if not ctx or not ctx.get('can_interview'):
        print("⚠️ No interview context available.")
        return

    print(f"ℹ️ {ctx['prompt']}")
    choice = input("\n👉 Do you want to start the interview? (y/n): ").strip().lower()
    
    if choice != 'y':
        print("\n👋 Skipping interview.")
        return

    # Start Interview
    payload = ctx['payload']
    print("\n🔄 Initializing session...")
    
    try:
        res = requests.post(f"{BASE_URL}/interview/start", json=payload)
        if res.status_code != 200:
             print(f"❌ Error starting interview: {res.text}")
             return
             
        session_data = res.json()
        session_id = session_data['session_id']
        
        print(f"🎯 Role Detected: {session_data['role']}")
        print(f"\n🤖 AI: {session_data['question']}")
        
        while True:
            answer = input("\n👤 You: ")
            if not answer.strip():
                print("⚠️ Please provide an answer.")
                continue
                
            res = requests.post(f"{BASE_URL}/interview/answer", json={
                "session_id": session_id,
                "answer": answer
            })
            
            resp_data = res.json()
            
            # Show feedback
            score = resp_data.get('score', 0)
            feedback = resp_data.get('feedback', '')
            print(f"\n📝 Feedback: {feedback} (Score: {score}/10)")
            
            if resp_data['is_finished']:
                print("\n✅ Interview Finished.")
                break
                
            print(f"\n🤖 AI: {resp_data['next_question']}")
            
        # Get Final Results
        res = requests.post(f"{BASE_URL}/interview/result", json={"session_id": session_id})
        final = res.json()
        
        print_header("STEP 3: FINAL EVALUATION")
        print(f"📄 Resume Score (30%):    {final['resume_score']}")
        print(f"🎤 Interview Score (70%): {final['interview_score']}")
        print("-" * 30)
        print(f"🏆 FINAL RANKING SCORE:   {final['final_score']} / 100")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during interview: {e}")

def main():
    match_data = step_match_resume()
    step_interview(match_data)

if __name__ == "__main__":
    main()
