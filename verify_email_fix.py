import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.utils import send_mail

def test_email():
    load_dotenv()
    
    recipient = os.getenv('SMTP_USER')
    if not recipient:
        print("❌ Error: SMTP_USER not found in .env. Cannot test.")
        return

    provider = os.getenv('EMAIL_PROVIDER', 'smtp')
    print(f"🚀 Testing Email Sending (Provider: {provider})...")
    
    subject = f"Verification Test - {provider.upper()}"
    body = f"This is a test email sent using the centralized send_mail function via {provider}."
    
    success = send_mail(
        subject=subject,
        recipient=recipient,
        body_text=body,
        sender_name="Portfolio Test"
    )
    
    if success:
        print(f"✅ SUCCESS: Email sent via {provider} to {recipient}")
    else:
        print(f"❌ FAILED: Email failed via {provider}")

if __name__ == "__main__":
    test_email()
