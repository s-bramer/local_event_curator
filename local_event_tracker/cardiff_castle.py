from bs4 import BeautifulSoup
from bs4.element import Comment
from datetime import datetime
from datetime import date
import calendar
import requests
import re

#set up variables
url="https://www.cardiffcastle.com/events/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'}
entries = []
all_events= []
WEEKDAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def tag_visible(element):
    """checks whether text is visible"""
    print(element)
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    if element == "":
        return False
    return True

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
container = soup.find("div", class_="ajaxwrap")
for tag in container.find_all(href=re.compile('/events/')):
    all_events.append(tag.get('href'))


#remove duplicate events
all_events = list(dict.fromkeys(all_events))
print(all_events)
#load each events page and scrape the events details 
for link in all_events:
    url = link
    r=requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "html5lib")
    container = soup.find('div', class_ ='singlewrap')
    title = container.find('h1', class_ ='singlewrap-title FadeIn').text.strip()
    full_date = container.find_all('p', class_ ='eventdetail-text')[0].text.replace('\n', ' ').strip()
    start = format_date(full_date.split('-')[0])
    if len(full_date.split('-')) == 2:
        end = format_date(full_date.split('-')[1])
    else:
        end = start
    if len(container.find_all('p', class_ ='eventdetail-text')) == 3:
        full_time = container.find_all('p', class_ ='eventdetail-text')[1].text.replace('\n', ' ').strip()
        time_start = format_time(full_time.split('-')[0])
        if len(full_time.split('-')) == 2:
            time_end = format_time(full_time.split('-')[1])
        else:
            time_end = time_start
        address = container.find_all('p', class_ ='eventdetail-text')[2].text.replace('\n', ' ').strip()
    else:
        time_start = datetime.strptime("00:00","%H:%M")
        time_end = datetime.strptime("00:00","%H:%M")
        address = container.find_all('p', class_ ='eventdetail-text')[1].text.replace('\n', ' ').strip()
    container = soup.find('div', class_ ='usercontent')
    event_info_text = ' '.join([str(item.text).replace(u'\xa0', u' ') for item in container.find_all("p")])

    entries.append({'url': url, 'title': title, 'start_date': start.strftime("%d/%m/%Y"), 'end_date': end.strftime("%d/%m/%Y"), 'time_start':time_start.strftime("%H:%M"), 'time_end':time_end.strftime("%H:%M"), 'address': address,'info': event_info_text})
print(entries)

