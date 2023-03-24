import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

smtp_port = 587
smtp_server = "smtp.gmail.com"

TSU_EMAIL = "EMAIL"
email_name = ["NAME ARRAY"]

pswd = "I am not putting that "

def send_emails(students, sub, body):

    for person in students:
        body = body.replace("^", person[1])

        msg = MIMEMultipart()
        msg['From'] = TSU_EMAIL
        msg['To'] = person[2]
        msg['Subject'] = sub

        msg.attach(MIMEText(body, 'plain'))

        text = msg.as_string()

        TIE_server = smtplib.SMTP(smtp_server, smpt_port)
        TIE_server.starttls()
        TIE_server.login(TSU_EMAIL, pswd)



        TIE_server.sendmail(TSU_EMAIL, person, text)

    # Closes the port
    TIE_server.quit()

test_subject = "TESTING"
test_body = "Hello ^,\n\tThis is a test email so I hope this works. Please reply to this email ASAP so I know it works.\nThanks,\nACS Tech Startup Club (TSU)"
test_students = [
    (0, "Rohit Sundararaman", "rohitsundararaman@acs.sch.ae", 10, "M")
]

print(test_body.replace('^', test_students[0][1]))
#send_emails(test_students, test_subject, test_body)