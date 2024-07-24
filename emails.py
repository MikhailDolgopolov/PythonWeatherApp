import smtplib, ssl






title = "Погода на сегодня и завтра"



from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
message = MIMEMultipart("alternative")
message["Subject"] = "Погода"
message["From"] = sender_email
message["To"] = receiver_email


def send_selenium_html(HTML_element):
    source_code = HTML_element.get_attribute("outerHTML")
    plain_text = HTML_element.text
    port = 465

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(plain_text, "plain")
    part2 = MIMEText(source_code, "html")

    message.attach(part1)
    message.attach(part2)

    print(part2)

    # context = ssl.create_default_context()
    # with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    #     server.login(sender_email, password)
    #     server.sendmail(sender_email, receiver_email, message.as_string())

# send_Selenium_HTML(elem)
