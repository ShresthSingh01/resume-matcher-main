import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load config from environment or use placeholders
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

def send_interview_invite(candidate_email: str, candidate_name: str, candidate_id: str):
    """
    Sends an email invitation with a unique interview link.
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"⚠️ Email Config Missing. Skipping email to {candidate_email}.")
        print(f"🔗 Mock Link: {BASE_URL}/interview/start?candidate_id={candidate_id}")
        return

    interview_link = f"{BASE_URL}/interview/start?candidate_id={candidate_id}"

    subject = "Interview Invitation: AI Resume Matcher"
    body = f"""
    Hi {candidate_name},

    Thank you for applying. We were impressed by your profile and would like to invite you to a preliminary AI-conducted interview.

    Please click the link below to start your interview at your convenience:
    {interview_link}

    Good luck!
    
    Best regards,
    The Hiring Team
    """

    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = candidate_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, candidate_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {candidate_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {candidate_email}: {e}")
