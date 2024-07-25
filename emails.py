import smtplib, ssl
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def read_config(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


# Example usage
config_path = 'email_secrets.json'
config = read_config(config_path)

sender_email, receiver_email = config["sender_email"], config["receiver_email"]


title = "Погода на сегодня и завтра"

message = MIMEMultipart("alternative")
message["Subject"] = "Погода"
message["From"] = sender_email
message["To"] = receiver_email


def send_my_email():
    port = 465

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(plain_text, "plain")
    part2 = MIMEText(source_code, "html")

    message.attach(part1)
    message.attach(part2)

    print(part2)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender_email, config["password"])
        server.sendmail(sender_email, receiver_email, message.as_string())

# send_Selenium_HTML(elem)
