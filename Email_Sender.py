import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

smtp_port = 587
smtp_server = "smtp.gmail.com"

email_from = "EMAIL"
email_list = ["EMAIL ARRAY"]
email_name = ["NAME ARRAY"]

pswd = "I am not putting that "

def send_emails(email_list):

    for person in email_list:

        subject = "subject"

        body = f"""
        Dear , You have signed up for {trip}. How fun! For your trip, you must select people you would like to be roommates with. Please fill in the form below to choose your roommates.
        """

        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = person
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        text = msg.as_string()

        TIE_server = smtplib.SMTP(smtp_server, smpt_port)
        TIE_server.starttls()
        TIE_server.login(email_from, pswd)



        TIE_server.sendmail(email_from, person, text)

    # Closes the port
    TIE_server.quit()


send_emails(email_list)