import re
from redmail import gmail
import smtplib
import ssl
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Union

from Day import Day
from helpers import read_json

config = read_json('mail/secrets.json')


def read_receivers():
    # mishad2304+python@gmail.com
    # dolgpa+python@gmail.com
    # midolgop@yandex.ru
    # dolgtat@yandex.ru
    addresses = open("mail/receivers.txt").read().split("\n")
    return addresses


# noinspection SpellCheckingInspection
def send_my_email(today: Dict[str, Union[str, Day]], tomorrow: Dict[str, Union[str, Day]]):
    print("Creating and sending the email")
    metadata = read_json("metadata.json")
    port = 465

    message = MIMEMultipart("related")
    message["Subject"] = f"Погода в {today['day'].accs_day_name} и {tomorrow['day'].accs_day_name}"
    message["From"] = config["gmail_email"]

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
        dates.append(
            datetime.strptime(metadata[day['day'].short_date], '%Y-%m-%dT%H:%M:%S').strftime("%d.%m.%Y, в %H:%M:%S"))
    # noinspection SpellCheckingInspection
    html = html.format(f"Данные получены {dates[0]}", f"Данные получены {dates[1]}")
    message.attach(MIMEText(html, "text/html", "utf-8"))
    message.attach(MIMEText(html, "text/plain", "utf-8"))

    with open(today["path"], "rb") as img1:
        mime_img1 = MIMEImage(img1.read(), _subtype="png")
        mime_img1.add_header("Content-ID", "<figure1>")
        message.attach(mime_img1)
    with open(tomorrow["path"], "rb") as img2:
        mime_img2 = MIMEImage(img2.read(), _subtype="png")
        mime_img2.add_header("Content-ID", "<figure2>")
        message.attach(mime_img2)

    context = ssl.create_default_context()

    rec_str = ", ".join(read_receivers())
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as s:
            s.login(config["gmail_email"], config[f"gmail_password"])
            message["To"] = rec_str
            s.sendmail(message["From"], rec_str, message.as_string())
            print(f"email(s) sent to {rec_str}")
            s.quit()
    except Exception as e:
        print(f"Failed to send:")
        print(e)
    finally:
        print("Done with emails")


def send_red_email(today: Dict[str, Union[str, Day]], tomorrow: Dict[str, Union[str, Day]], receivers=None):
    gmail.username = config["gmail_email"]
    gmail.password = config["gmail_password"]
    if receivers is None:
        receivers = read_receivers()
    metadata = read_json("metadata.json")
    dates = []
    for day in [today, tomorrow]:
        dates.append(
            datetime.strptime(metadata[day['day'].short_date], '%Y-%m-%dT%H:%M:%S').strftime("%d.%m.%Y, в %H:%M:%S"))

    html = """
        <div style="width=90%">
            <img src = "{{plot1.src}}" width="70%"/>
            <p style="margin-left:5%">{{note1}}</p>
        </div>
        <p><br></br>
        </p>
        <div style="width=90%">
            <img src = "{{plot2.src}}" width="70%"/>
            <p style="margin-left:5%">{{note2}}</p>
        </div>
        """

    gmail.send(
        subject=f"Погода в {today['day'].accs_day_name} и {tomorrow['day'].accs_day_name}",
        sender=config["gmail_email"],
        receivers=receivers,
        html=html,
        body_images={"plot1": today["path"],
                     "plot2": tomorrow["path"]},
        body_params={"note1":f"Данные получены {dates[0]}",
                     "note2":f"Данные получены {dates[1]}"}
    )
    print(f"Sent to {receivers}")
    print("Done with emails")
