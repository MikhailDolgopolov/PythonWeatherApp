import os.path
import os
from glob import glob
from datetime import datetime, timedelta
import re


def delete_old_files():
    folders = ["forecast", "Images"]
    date = datetime.today() - timedelta(days=1)
    number = int(date.strftime("%Y%m%d"))
    to_delete = []
    for folder in folders:
        for file in glob(f'{folder}\\*.*'):
            match = re.search(r'\d+', file)
            if match and int(match.group()) < number:
                to_delete.append(file)
    for p in to_delete:
        os.remove(p)
    print(f"Removed {len(to_delete)} files.")
