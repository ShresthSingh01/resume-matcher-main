import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load config from environment or use placeholders
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")

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
    interview_link = f"{BASE_URL}/candidate?candidate_id={candidate_id}"
    subject = "Next Step in Your Application Process: Invitation to AI Interview"
    body = f"""
    Hi {candidate_name},
    Thank you for applying to Virex and for the time you’ve invested in your application.
    Based on our initial review, we’d like to continue learning more about your profile. As part of the next step, we invite you to complete a short AI-assisted interview that will help us better understand your skills and experience.
    You can begin the interview at a time that’s convenient for you using the link below:
    {interview_link}
    We appreciate your interest in Virex and look forward to reviewing your responses.
    Best regards,
    The Hiring Team Virex
    """
    _send_email(candidate_email, subject, body)

def send_shortlist_email(candidate_email: str, candidate_name: str):
    """
    SHORTLIST: Congratulations & Next Steps.
    """
    subject = "Congratulations! You are Shortlisted for the Next Round"
    body = f"""
    Hi {candidate_name},
    Thank you for your interest in joining Virex and for taking the time to apply.
    We’re happy to let you know that your profile has been reviewed and selected to move forward to the next stage of our hiring process. Your experience and background stood out, and we’d like to learn more about you.
    Our HR team will reach out to you shortly to schedule a one-on-one conversation and share further details.
    We look forward to connecting with you.
    Best regards,
    The Hiring Team Virex 
    """
    _send_email(candidate_email, subject, body)

def send_rejection_email(candidate_email: str, candidate_name: str, job_suggestions: list = []):
    """
    REJECTED: Better luck next time + Job Suggestions.
    """
    subject = "Update on your application"
    
    jobs_section = ""
    if job_suggestions and len(job_suggestions) > 0:
        jobs_section = "\n\n    Here are some other opportunities that might be a great fit for your profile:\n"
        for job in job_suggestions:
            title = job.get('title', 'Job Opening')
            company = job.get('company', 'Unknown Company')
            link = job.get('url', '#')
            jobs_section += f"    - {title} at {company}: {link}\n"
    
    body = f"""
    Hi {candidate_name},
    Thank you for taking the time to apply to Virex and for your interest in joining our team.
    After careful review, we’ve decided to proceed with other candidates for this role at this time. This decision was not easy, and we truly appreciate the effort and thought you put into your application.
    We were glad to learn more about your background, and we encourage you to stay connected with us and apply again in the future as new opportunities arise. We wish you all the best in your continued journey.{jobs_section}
    Warm regards,
    The Hiring Team Virex
    """
    _send_email(candidate_email, subject, body)
