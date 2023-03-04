import re
import dns.resolver
import smtplib

def verify_email(email):
    # Verify email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    
    # Extract domain from email
    domain = email.split('@')[1]
    
    try:
        # Check domain MX records
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = records[0].exchange.to_text()

        # Connect to SMTP server
        smtp_server = smtplib.SMTP()
        smtp_server.connect(mx_record)
        smtp_server.helo(smtp_server.local_hostname)
        smtp_server.mail('test@test.com')
        response = smtp_server.rcpt(email)
        smtp_server.quit()

        # Email is valid if SMTP server accepts it
        if response[0] == 250:
            return True
        else:
            return False
    except:
        return False

print(verify_email("hyungjae1130@gmail.com"))