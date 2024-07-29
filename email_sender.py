from datetime import datetime
from typing import Dict, Union

from redmail import gmail

from Day import Day
from ForecastRendering import get_and_render
from helpers import read_json

config = read_json('secrets.json')


def read_receivers():
    # mishad2304+python@gmail.com
    # dolgpa+python@gmail.com
    # midolgop@yandex.ru
    # dolgtat@yandex.ru
    addresses = open("mail/receivers.txt").read().split("\n")
    return addresses


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



