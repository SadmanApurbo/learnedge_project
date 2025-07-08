import smtplib
from email.message import EmailMessage

def send_reset_email(to_email, reset_link):
    msg = EmailMessage()
    msg['Subject'] = 'LearnEdge Password Reset'
    msg['From'] = 'sadman.sakibrda@gmail.com'  # Replace with your email
    msg['To'] = to_email
    msg.set_content(f"Click this link to reset your password: {reset_link}")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('sadman.sakibrda@gmail.com', 'xxsu wnfh iqaq zunh')  # Replace with your app password
        smtp.send_message(msg)
