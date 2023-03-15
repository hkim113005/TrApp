import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

smpt_port = 587
smtp_server = "smtp.gmail.com"

email_from = "EMAIL"
email_to = ["EMAIL ARRAY"]
email_name = ["NAME ARRAY"]

pswd = "I am not putting that "

def send_emails(email_list):

    for person in email_list:

        subject = "subject"

        body = f"""
        Kaboom
        """ + person + " KOOL"

        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = person
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        text = msg.as_string()

        TIE_server = smtplib.SMTP(smtp_server, smtp_port)
        TIE_server.starttls()
        TIE_server.login(email_from, pswd)



        TIE_server.sendmail(email_from, person, text)

    TIE_server.quit()


send_emails(email_list)