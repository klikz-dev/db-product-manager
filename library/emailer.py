import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email_text(recipient, subject, body):
    gmail_user = 'murrell@decoratorsbest.com'
    gmail_pwd = 'yqebhktdnalqpkfl'

    FROM = 'murrell@decoratorsbest.com'
    TO = recipient
    SUBJECT = subject
    TEXT = body

    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server_ssl.ehlo()
    server_ssl.login(gmail_user, gmail_pwd)
    server_ssl.sendmail(FROM, TO, message)
    server_ssl.close()


def send_email_html(sender, recipient, subject, body):
    if isinstance(recipient, list):
        for receiver in recipient:
            gmail_user = "murrell@decoratorsbest.com"
            gmail_pwd = 'yqebhktdnalqpkfl'

            message = MIMEMultipart()
            message["From"] = sender
            message["To"] = receiver
            message["Subject"] = subject
            html = MIMEText(body, "html")
            message.attach(html)

            server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server_ssl.ehlo()
            server_ssl.login(gmail_user, gmail_pwd)
            server_ssl.sendmail(sender, receiver, message.as_string())
            server_ssl.close()
    else:
        receiver = recipient

        gmail_user = "murrell@decoratorsbest.com"
        gmail_pwd = 'yqebhktdnalqpkfl'

        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = receiver
        message["Subject"] = subject
        html = MIMEText(body, "html")
        message.attach(html)

        server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server_ssl.ehlo()
        server_ssl.login(gmail_user, gmail_pwd)
        server_ssl.sendmail(sender, receiver, message.as_string())
        server_ssl.close()
