#THIS FILE IS JUST FOR TESTING CODE#
#DELETE ME!!#
import re
import pandas as pd
import time
import calendar
from datetime import date, datetime
import numpy as np

# def findElements(lst1, lst2):
#     return list(np.array(lst1)[lst2])

# indices = [0,1]

# list_of_things = ['apple','bana','plums','berry']


# print(findElements(list_of_things,indices))

# conns = '–;&'
# #print(conns.split(';'))
# print('& 'in conns)

# print(int("stef"))

# text = "8th"
# print(text[-2:])
# ordinals = ['th', 'st', 'nd', 'rd']
# #print(any(ordinal in text for ordinal in ordinals))


# dicard_list_title = ['Cancelled', 'Luminatae']
# discard_list_location = ['Fully\sBooked']
# df = pd.read_csv("events_database.csv", header=0, index_col=None)

# # df = df[df["title"].str.contains('|'.join(dicard_list_title)) == False]
# # df = df[df["location"].str.contains('|'.join(discard_list_location)) == False]

# #df.drop_duplicates(subset=['title','location'],keep='first', inplace=True,ignore_index=True)
# df = df.loc[(df['end_date'] >= date.today().strftime('%Y-%m-%d'))]

# df_out_path = "events_database_ppp.csv"
# df.to_csv(df_out_path,index=False)

category = "exhibition:"
print(category)
if category[-1] == ':':
    category = category[:-1]
print(category)