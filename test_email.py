import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

sender = os.environ.get("EMAIL_ADDRESS")
smtp_login = os.environ.get("BREVO_SMTP_LOGIN")
smtp_key = os.environ.get("BREVO_SMTP_KEY")

print("Sender:", sender)
print("SMTP login:", smtp_login)
print("SMTP key length:", len(smtp_key) if smtp_key else "MISSING")

msg = MIMEText("This is a test email from Nexus Analyst.")
msg["Subject"] = "Test Email"
msg["From"] = sender
msg["To"] = sender

try:
    with smtplib.SMTP("smtp-relay.brevo.com", 587) as server:
        server.starttls()
        server.login(smtp_login, smtp_key)
        server.sendmail(sender, [sender], msg.as_string())
    print("SUCCESS: Email sent!")
except Exception as e:
    print("FAILED:", e)