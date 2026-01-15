import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

def test_email_sending():
    server_host = os.getenv("SMTP_SERVER")
    port = int(os.getenv("SMTP_PORT", 587))
    username = os.getenv("SMTP_USERNAME")
    # Apply the same fix as in the main app
    password = os.getenv("SMTP_PASSWORD", "").replace(" ", "")

    print(f"🔍 Testing Email Sending...")
    print(f"   Host: {server_host}:{port}")
    print(f"   User: {username}")

    if not username or not password:
        print("❌ Error: SMTP params missing.")
        return

    msg = MIMEText("This is a test email from your Resume Matcher app to verify SMTP settings.")
    msg['Subject'] = "Resume Matcher SMTP Test"
    msg['From'] = username
    msg['To'] = username  # Send to self

    try:
        server = smtplib.SMTP(server_host, port)
        server.starttls()
        server.login(username, password)
        print("✅ Login Successful")
        
        server.sendmail(username, username, msg.as_string())
        print(f"✅ Test email sent to {username}")
        server.quit()
        
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_email_sending()
