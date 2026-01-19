
from app.email_service import send_rejection_email
import sys

# Mock _send_email to print instead of send
import app.email_service as es

def mock_send_email(to, subject, body):
    print(f"--- EMAIL TO {to} ---")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("---------------------")

es._send_email = mock_send_email

# Test Case 1: No jobs
print("\nTest 1: Rejection NO Jobs")
send_rejection_email("test@example.com", "John Doe", [])

# Test Case 2: With Jobs
print("\nTest 2: Rejection WITH Jobs")
jobs = [
    {"title": "Software Engineer", "company": "Tech Corp", "url": "http://example.com/job1"},
    {"title": "Backend Developer", "company": "StartUp Inc", "url": "http://example.com/job2"}
]
send_rejection_email("test@example.com", "Jane Doe", jobs)
