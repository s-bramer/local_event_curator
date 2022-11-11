#THIS FILE IS JUST FOR TESTING CODE#
#DELETE ME!!#

import csv
from csv import DictReader
import re
import pandas as pd

with open('./events_database_update.csv', newline='', encoding="utf8") as csv_file:
    csv_data = DictReader(csv_file)
    list_of_events = list(csv_data)

unique_list = list({ item['name'] : item for item in list_of_events}.values())
for item in unique_list:
    print(item['name'])
