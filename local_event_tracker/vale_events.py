from bs4 import BeautifulSoup
from bs4.element import Comment
from datetime import datetime
from datetime import date
import calendar
import requests
import re

#set up variables
url="https://www.visitthevale.com/events"
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

def tag_visible(element):
    """checks whether text is visible"""
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True
def get_address(list):
    """extract address info from visitvale.com for specific event"""
    append = False
    address = []
    for element in list:
        if append and element != "View on map":
            address.append(element)
        if element == "View on map":
            append = False
        elif element == "Address":
            append = True
    return address

# #get all links to events page (all events)  
# r=requests.get(url, headers=headers)
# soup = BeautifulSoup(r.content, "html5lib")
# for tag in soup.find_all(href=re.compile('/events/')):
#     all_events.append(tag.get('href'))

# #remove duplicate events
# all_events = list(dict.fromkeys(all_events))

#load each events page and scrape the events details 
# for link in all_events:
#     url=f"https://www.visitthevale.com{link}"
#     r=requests.get(url, headers=headers)
#     soup = BeautifulSoup(r.content, "html5lib")
#     title = soup.title.string.split("|")[0].strip()
#     container = soup.find("div", class_="grid-container") #get event info container
#     event_info_text = ', '.join([str(item.text.replace(u'\xa0', u' ')) for item in container.find_all("div", class_="w-richtext")]) #get all text within event info containter
#     container = soup.find("div", class_="grid-item-50") #get event details container
#     texts = container.findAll(text=True)
#     visible_texts = filter(tag_visible, texts) 
#     event_information = u"||".join(t.strip() for t in visible_texts) # get all visible text from event container (u = unicode)
#     start = format_date(event_information.split("||")[2])
#     end = format_date(event_information.split("||")[4])
#     address = get_address(event_information.split("||"))
#     entries.append({'url': url, 'title': title, 'start_date': start.strftime("%d/%m/%Y"), 'end_date': end.strftime("%d/%m/%Y"), 'address': address, 'info': event_info_text})
# print(entries)
#EVENT INFO TEXT FORMATTING IS STILL OFF

url="https://www.visitthevale.com/events/halloween-at-fonmon-night-scare-trail"
r=requests.get(url, headers=headers)
soup = BeautifulSoup(r.content, "html5lib")
title = soup.find('h1', class_ ='').text.strip()
print(title)
# container = soup.find("div", class_="grid-container") #get event info container
# event_info_text = ', '.join([str(item.text) for item in container.find_all("div", class_="w-richtext")])
# print(event_info_text)

<meta content="VALE PICK YOUR OWN – HALLOWEEN 2022  | Visit The Vale" property="og:title">