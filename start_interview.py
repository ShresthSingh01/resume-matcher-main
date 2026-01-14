import asyncio
import os
from app.resume_parser import parse_resume
from app.matcher import extract_skills, calculate_match_score
from app.embeddings import check_duplicate, load_initial_embeddings
from app.interview_manager import interview_manager
from app.db import init_db

def clean_input(prompt):
    return input(prompt).strip()

def main():
    print("🧠 AI Resume Matcher & Interviewer CLI")
    print("========================================")
    
    # Init
    init_db()  # Ensure DB exists
    
    # 1. Upload
    resume_path = clean_input("Enter path to Resume (PDF/TXT): ")
    if not os.path.exists(resume_path):
        print("❌ File not found.")
        return

    jd_path = clean_input("Enter path to Job Description (TXT) or 'paste' to enter text: ")
    
    resume_text = ""
    with open(resume_path, "rb") as f:
        content = f.read()
        resume_text = parse_resume(content, resume_path)

    jd_text = ""
    if jd_path.lower() == 'paste':
        print("Paste JD below (Ctrl+D or Ctrl+Z to finish):")
        import sys
        jd_text = sys.stdin.read().strip()
    elif os.path.exists(jd_path):
         with open(jd_path, "rb") as f:
            content = f.read()
            # If it's a file, parse it (could be PDF too technically)
            jd_text = parse_resume(content, jd_path)
    else:
        print("❌ Invalid JD input.")
        return

    if not resume_text or not jd_text:
        print("❌ Failed to extract text.")
        return

    print("\n🔍 Analyzing...")

    # 3. Duplicate
    if check_duplicate(resume_text):
        print("⚠️ Warning: This resume is a potential duplicate.")

    # 4. Match
    match_data = extract_skills(resume_text, jd_text)
    score = calculate_match_score(
        match_data['matched_skills'],
        match_data['missing_skills'],
        resume_text=resume_text,
        jd_text=jd_text
    )

    print(f"\n📊 Match Score: {score}%")
    print(f"✅ Matched: {', '.join(match_data['matched_skills'])}")
    print(f"❌ Missing: {', '.join(match_data['missing_skills'])}")
    
    # 5. Interview
    choice = clean_input("\n🎤 Start AI Interview? (y/n): ").lower()
    if choice != 'y':
        print("Exiting.")
        return

    print("\n🤖 Assistant: Preparing interview...")
    session = interview_manager.create_session(resume_text, jd_text, score)
    
    # Start
    q = interview_manager.start_interview(session.session_id)
    print(f"\n🤖 Assistant: {q}")

    while True:
        ans = clean_input("\n👤 You: ")
        
        # Process
        print("Processing answer...")
        next_q, is_done, feedback, step_score = interview_manager.process_answer(session.session_id, ans)
        
        print(f"   [Score: {step_score}/10 | Feedback: {feedback}]")

        if is_done:
            print(f"\n✅ {next_q}") # "Interview Complete"
            break
        
        print(f"\n🤖 Assistant: {next_q}")

    # Final Result
    res = interview_manager.calculate_final_result(session.session_id)
    print("\n🎓 Final Report")
    print("=================")
    print(f"Resume Score: {res['resume_score']}")
    print(f"Interview Score: {res['interview_score']}")
    print(f"FINAL SCORE: {res['final_score']}")
    print("=================")
    
if __name__ == "__main__":
    main()
