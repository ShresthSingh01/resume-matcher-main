import requests
import os
import sys
import time
import pyttsx3
import threading

BASE_URL = "http://127.0.0.1:8000"
RESUME_FILE = "resume.pdf"
JD_FILE = "jd.txt"

def print_header(title):
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)


def speak_text(text):
    """
    Speak the text using pyttsx3.
    Use a fresh engine instance each time to avoid loop issues.
    """
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        # Explicitly stop the engine (though runAndWait should handle it)
        engine.stop()
        del engine
    except Exception as e:
        # Fallback if TTS fails
        pass
def step_match_resume():
    print_header("STEP 1: RESUME MATCHING")
    
    if not os.path.exists(RESUME_FILE) or not os.path.exists(JD_FILE):
        print(f"❌ Error: Ensure {RESUME_FILE} and {JD_FILE} exist.")
        sys.exit(1)
        
    print(f"📄 Uploading {RESUME_FILE} and {JD_FILE}...")
    
    files = {
        "resume": (os.path.basename(RESUME_FILE), open(RESUME_FILE, "rb")),
        "jd_file": (os.path.basename(JD_FILE), open(JD_FILE, "rb"))
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload", files=files)
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            sys.exit(1)
            
        data = response.json()
        print("\n✅ Match Complete!")
        print(f"   Match Score: {data['match_score']}/100")
        print(f"   Skills Found: {', '.join(data['matched_skills'][:5])}...")
        print(f"   Skills Missing: {', '.join(data['missing_skills'][:5])}...")
        
        return data
    except Exception as e:
        print(f"❌ Connection Error: {e}")
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
        print("-" * 30)
        print(f"🏁 FINAL SCORE: {context_data['match_score']} (Resume Only)")
        return

    # Start Interview
    payload = ctx['payload']
    print("\n🔄 Initializing specific interview session...")
    
    try:
        res = requests.post(f"{BASE_URL}/interview/start", json=payload)
        session_data = res.json()
        session_id = session_data['session_id']
        
        print(f"🎯 Role Detected: {session_data['role']}")
        print(f"\n🤖 AI: {session_data['question']}")
        speak_text(session_data['question'])
        
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
            
            # Show immediate feedback
            feedback = resp_data.get('feedback', 'No feedback')
            score = resp_data.get('score', 0)
            print(f"\n📝 Feedback: {feedback} (Score: {score}/10)")
            
            if resp_data['is_finished']:
                print("\n✅ Interview Finished.")
                break
                
            print(f"\n🤖 AI: {resp_data['next_question']}")
            speak_text(resp_data['next_question'])
            
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
