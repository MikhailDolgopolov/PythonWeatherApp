import re
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
    addresses = open("mail/receivers.txt").read().split("\n")
    pattern = re.compile(r".*@(.*\..{2,3})$")
    corresponding = {a: re.search(pattern, a).group(1) for a in addresses}
    servers = set(corresponding.values())
    server_mapping = {"smtp." + k: [ad for ad, ser in corresponding.items() if ser == k] for k in servers}
    print("Looked up receivers")

    return server_mapping


# noinspection SpellCheckingInspection
def send_my_email(today: Dict[str, Union[str, Day]], tomorrow):
    print("Creating and sending the email")
    metadata = read_json("metadata.json")
    port = 465

    message = MIMEMultipart("alternative")
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

    for server, ad_list in read_receivers().items():
        if server == "smtp.gmail.com": continue
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as s:
                s.login(config["gmail_email"], config[f"gmail_password"])
                rec_str = ", ".join(ad_list)
                message["To"] = rec_str
                # print(message["To"])
                s.sendmail(message["From"], rec_str, message.as_string())
                print(f"email(s) sent to {server}")
        except Exception as e:
            print(f"Failed to send to {server}:")
            print(e)
        finally:
            print("Done with emails")
