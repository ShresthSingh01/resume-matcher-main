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

def _send_email(to_email, subject, body):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"⚠️ Email Config Missing. Skipping email to {to_email}.")
        print(f"Subject: {subject}")
        print(f"Body: {body[:100]}...")
        return

    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")

def send_interview_invite(candidate_email: str, candidate_name: str, candidate_id: str):
    """
    WAITLIST / INTERVIEW: Sends AI Interview Invite.
    """
    interview_link = f"{BASE_URL}/interview/start?candidate_id={candidate_id}"
    subject = "Update on your application: Invitation to AI Interview"
    body = f"""
    Hi {candidate_name},

    Thank you for your application. Based on our initial review, we have placed you on our Waitlist for the role.
    
    To help us assess your fit further, we explicitly invite you to take a preliminary AI-conducted interview.
    
    Please click the link below to start:
    {interview_link}

    Best regards,
    The Hiring Team
    """
    _send_email(candidate_email, subject, body)

def send_shortlist_email(candidate_email: str, candidate_name: str):
    """
    SHORTLIST: Congratulations & Next Steps.
    """
    subject = "Congratulations! You are Shortlisted for the Next Round"
    body = f"""
    Hi {candidate_name},

    We are pleased to inform you that your resume has been Shortlisted for the position!
    
    Your profile stood out among the applicants, and we would like to move you to the next round of our hiring process.
    Our HR team will reach out to you shortly to schedule a 1-on-1 discussion.

    Congratulations again!
    
    Best regards,
    The Hiring Team
    """
    _send_email(candidate_email, subject, body)

def send_rejection_email(candidate_email: str, candidate_name: str):
    """
    REJECTED: Better luck next time.
    """
    subject = "Update on your application"
    body = f"""
    Hi {candidate_name},

    Thank you for your interest in our company and for taking the time to apply.
    
    After carefully reviewing your application, we regret to inform you that we will not be moving forward with your candidacy at this time.
    We appreciate your effort and wish you the best of luck in your job search.

    Best regards,
    The Hiring Team
    """
    _send_email(candidate_email, subject, body)
