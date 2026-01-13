import requests
import os

URL = "http://127.0.0.1:8000/upload"
RESUME_FILE = "resume.pdf"
JD_FILE = "jd.txt"

def run_matcher():
    if not os.path.exists(RESUME_FILE):
        print(f"❌ Error: {RESUME_FILE} not found in this directory.")
        return
    if not os.path.exists(JD_FILE):
        print(f"❌ Error: {JD_FILE} not found in this directory.")
        return

    print(f"🚀 Processing: {RESUME_FILE} + {JD_FILE}")
    
    files = {
        "resume": (os.path.basename(RESUME_FILE), open(RESUME_FILE, "rb")),
        "jd_file": (os.path.basename(JD_FILE), open(JD_FILE, "rb"))
    }
    
    try:
        response = requests.post(URL, files=files)
        if response.status_code == 200:
            result = response.json()
            print("\n✅ MATCH COMPLETED!")
            print("-" * 30)
            print(f"Score:          {result.get('match_score')}/100")
            print(f"Present Skills: {', '.join(result.get('matched_skills', []))}")
            print(f"Missing Skills: {', '.join(result.get('missing_skills', []))}")
            print("-" * 30)
            print(f"Explanation:\n{result.get('explanation')}")
            
            # Verify new Interview Context
            if 'interview_context' in result:
                print("\n🎯 INTERVIEW RECOMMENDATION:")
                print(result['interview_context']['prompt'])
                print(f"Payload Ready: {result['interview_context']['can_interview']}")
        else:
            print(f"\n❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    run_matcher()
