import pandas as pd
pd.set_option('display.width', 200)  # Increase the width to 200 characters
pd.set_option('display.max_columns', 10)  # Increase the number of columns to display to 10
pd.set_option('display.max_colwidth', 50)  # Set the max column width to 50 characters

from Parsers.OpenMeteo import get_open_meteo

openmeteo = pd.DataFrame.from_records(get_open_meteo(1), columns=["time", "temperature", "precipitation", "wind_speed"])
print(openmeteo)