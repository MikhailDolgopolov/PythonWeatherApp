import smtplib
import ssl
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Union

from Day import Day
from helpers import read_json

config = read_json('secrets.json')

sender_email, receiver_email = config["sender_email"], config["receiver_email"]



# noinspection SpellCheckingInspection
def send_my_email(today:Dict[str, Union[str, Day]], tomorrow):
    print("Creating and sending the email")
    metadata = read_json("metadata.json")
    port = 465

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Погода в {today['day'].accs_day_name} и {tomorrow['day'].accs_day_name}"
    message["From"] = sender_email
    message["To"] = receiver_email

    # noinspection SpellCheckingInspection
    html = """
    <html>
      <body>
    <div style="text-align: center; width: 100%;">
        <img style="width: 100%;" src="cid:figure1">
        <p style="text-align: center;">{0}</p>
    </div>
    <div style="text-align: center; width: 100%;">
        <img style="width: 100%;" src="cid:figure2">
        <p style="text-align: center;">{1}</p>
    </div>
      </body>
    </html>
    """

    dates = []
    for day in [today, tomorrow]:
        dates.append(datetime.strptime(metadata[day['day'].short_date],'%Y-%m-%dT%H:%M:%S').strftime("%d.%m.%Y, в %H:%M:%S"))
    # noinspection SpellCheckingInspection
    html = html.format(f"Данные получены {dates[0]}", f"Данные получены {dates[1]}")
    message.attach(MIMEText(html, "html"))

    with open(today["path"], "rb") as img1:
        mime_img1 = MIMEImage(img1.read(), _subtype="png")
        mime_img1.add_header("Content-ID", "<figure1>")
        message.attach(mime_img1)
    with open(tomorrow["path"], "rb") as img2:
        mime_img2 = MIMEImage(img2.read(), _subtype="png")
        mime_img2.add_header("Content-ID", "<figure2>")
        message.attach(mime_img2)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender_email, config["password"])
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent")

