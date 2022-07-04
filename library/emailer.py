import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email_text(recipient, subject, body):
    gmail_user = 'murrell@decoratorsbest.com'
    gmail_pwd = 'yqebhktdnalqpkfl'
    FROM = 'murrell@decoratorsbest.com'
    TO = 'murrell@decoratorsbest.com'
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
    gmail_user = "murrell@decoratorsbest.com"
    gmail_pwd = 'yqebhktdnalqpkfl'

    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = "murrell@decoratorsbest.com"
    message["Subject"] = subject
    html = MIMEText(body, "html")
    message.attach(html)

    server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server_ssl.ehlo()
    server_ssl.login(gmail_user, gmail_pwd)
    server_ssl.sendmail(sender, recipient, message.as_string())
    server_ssl.close()
