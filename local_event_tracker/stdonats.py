from bs4 import BeautifulSoup
from bs4.element import Comment
from datetime import datetime
from datetime import date
import calendar
import requests
import re

#set up variables
url="https://www.uwcatlanticexperience.com/event/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'}
entries = []
all_events= []
WEEKDAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def format_date(date_string):
    """convert date into proper date format"""
    date_string = date_string.replace(',',' ')
    date_list = date_string.split()
    if date_list[0] in WEEKDAYS:
        date_list.pop(0)
    # split into day/month/year
    day_string = date_list[0].strip()
    try: 
        month_string = date_list[1].strip()
    except:
        month_string = ""
        print("Soemthing went wrong. No event date (month) found....")
    try: 
        year = int(date_list[2].strip())
    except:
        year = date.today().year

    #DAY
    try:
        day = int(day_string)
    except:
        day = int(month_string)
        month_string = day_string
    #MONTH
    try:
        month = int(month_string)
    except:
        if len(month_string) == 3:
            month = list(calendar.month_abbr).index(month_string)
        else:
            month = list(calendar.month_name).index(month_string)
    return_date = date(year=year,month=month,day=day)
    
    return return_date

def format_time(time_string):
    return_time = datetime.strptime(time_string.strip(),"%H:%M")
    return return_time

#get all links to events page (all events)  
r=requests.get(url, headers=headers)
soup = BeautifulSoup(r.content, "html5lib")
for tag in soup.find_all(href=re.compile('eventbrite')):
    all_events.append(tag.get('href'))

#remove duplicate events
all_events = list(dict.fromkeys(all_events))
#print(all_events)

for link in all_events:
    url = link
    r=requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "html5lib")
    container = soup.find('div', attrs={"class": "event-details__wrapper"})
    title = container.find('h1', class_ ='event-title').text
    event_info_text = container.find('p', class_ ='summary').text
    start = time_start = datetime.fromisoformat(soup.find('meta', attrs={"data-testid": "event-start-date-tz"})["content"])
    end = time_end = datetime.fromisoformat(soup.find('meta', attrs={"data-testid": "event-end-date-tz"})["content"])
    address = "St Donat's Castle,  UWC Atlantic College Llantwit Major CF61 1WF"
    entries.append({'url': url, 'title': title, 'start_date': start.strftime("%d/%m/%Y"), 'end_date': end.strftime("%d/%m/%Y"), 'time_start':time_start.strftime("%H:%M"), 'time_end':time_end.strftime("%H:%M"), 'address': address,'info': event_info_text})
print(entries)
