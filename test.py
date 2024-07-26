import email
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pprint import pprint

import pandas as pd

from Day import Day
from Forecast import Forecast
from ForecastData import ForecastData
from helpers import read_json

pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters

from Parsers.OpenMeteo import get_open_meteo
from Parsers.ForecaParser import ForecaParser
import re
from datetime import datetime

# mishad2304+python@gmail.com
# dolgpa+python@gmail.com
# midolgop@yandex.ru
port = 465

config = read_json('mail/secrets.json')
rec_str=config["yandex_email"]
msg = email.message.Message()
# message = MIMEMultipart("related")
# message["Subject"] = f"Тест HTML"
# message["From"] = config["gmail_email"]
msg["Subject"] = "Тест HTML"
msg["To"] = rec_str
msg["From"] = config["gmail_email"]
msg.add_header('Content-Type','text/html')
msg.set_payload('Body of <b>message</b>')

# noinspection SpellCheckingInspection
html = """
<html>
  <body>
    <h1 style="color: blue; text-align: center;">Привет от Яндекс Почты!</h1>
    <p>Это тестовое письмо с <b>HTML-контентом</b>.</p>
    <p>Вот несколько примеров форматирования:</p>
    <ul>
      <li>Элемент списка 1</li>
      <li>Элемент списка 2</li>
    </ul>
    <p>И изображение:</p>
    <img src="https://www.example.com/image.jpg" alt="Example Image" style="width: 100%; max-width: 600px;">
  </body>
</html>
"""

# message.attach(MIMEText(html, "text/html", "utf-8"))
# message.attach(MIMEText(html, "text/plain", "utf-8"))



context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as s:
    s.login(config["gmail_email"], config[f"gmail_password"])

    s.sendmail(msg["From"], rec_str, msg.as_string())
    print(f"email(s) sent to {rec_str}")
    s.quit()

