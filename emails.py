import os
import smtplib
from email.message import EmailMessage


EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')


def email_notification(name, receiver_email, content):
    msg = EmailMessage()
    msg['Subject'] = f'{name} invites you to join Best Task Manager Bot'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = receiver_email
    msg.set_content(content)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_HOST_PASSWORD)
        smtp.send_message(msg)



