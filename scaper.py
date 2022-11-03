from events_tracker import Events
from bs4 import BeautifulSoup
from tabulate import tabulate
from datetime import date, datetime
import calendar
import requests
import pandas as pd
import re
import sys

# standard header for http request
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'}
# load event_pages CSV with links and search parameters
df = pd.read_csv("./local_event_tracker/event_pages.csv", header=0, index_col=None)
df_out = pd.DataFrame(columns=['link', 'title', 'start_date', 'end_date', 'location','info',])
df_out_path = r"./local_event_tracker/events_database.csv"
WEEKDAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def format_date(date_string):
    """convert date into proper date format"""
    date_string = date_string.replace(',',' ')
    date_list = date_string.split()
    # if first list item is the weekday, remove it
    if date_list[0] in WEEKDAYS:
        date_list.pop(0)
    # split into day/month/year
    day_string = date_list[0].strip()
    try: 
        month_string = date_list[1].strip()
    except:
        month_string = ""
        print("Something went wrong. No event date (month) found....")
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
    
    return return_date.strftime('%d/%m/%Y')

def format_time(time_string):
    return_time = datetime.strptime(time_string.strip(),"%H:%M")
    return return_time.strftime('%H:%M')

def get_all_events(link: str,  container: str, search: str, type="absolute", method="search"):
    """Returns all events urls from a webpage"""
    all_events = []
    response = requests.get(link, headers=headers)
    soup = BeautifulSoup(response.content, "html5lib")

    # if container passed step into it
    if not pd.isna(container):
        soup = soup.find("div", attrs={"class": container})
    # searching for a specific string in the href
    if method == "search":
        for tag in soup.find_all(href=re.compile(search)):
            all_events.append(tag.get('href'))
    # or directly targeting a specific tag
    elif method == "direct":
        for tag in soup.find_all('a', attrs={"class": search}):
            all_events.append(tag.get('href'))
    else:
        print("get_all_events, no valid method selected.")
        sys.exit()
    #remove duplicates from events
    all_events = list(dict.fromkeys(all_events))
    
    if type == "relative":
        all_events = [link + event.split('/')[-1] for event in all_events]

    return all_events

def get_date(soup, tag:str, attr:str, attr_name:str, date_split:int, start_end_date_split:str, start_end=0):
    if date_split != -999:
        full_date = soup.find_all(tag, attrs={attr: attr_name})[int(date_split)].text.replace('\n', ' ').strip()
    else:
        full_date = soup.find(tag, attrs={attr: attr_name}).text.replace('\n', ' ').strip()
    try:
        if start_end_date_split != "-999":
            date = format_date(full_date.split(start_end_date_split)[int(start_end)])
        else:
            date = format_date(full_date)
    except:
        date = ""
    return date

def get_time(soup, method:str, tag:str, attr:str, attr_name:str, time_split:int, start_end_time_split:str, start_end=0):
    # tag method when there is a specific tag in the body that contains the times
    if method == "tag":
        if time_split != -999:
            full_time = soup.find_all(tag, attrs={attr: attr_name})[int(time_split)].text.replace('\n', ' ').strip()
        else:
            full_time = soup.find(tag, attrs={attr: attr_name}).text.replace('\n', ' ').strip()
    
        try:
            time = format_time(full_time.split(start_end_time_split)[int(start_end)])
        except:
            time = ""
    # meta method when times are most accessible in the meta tags in the header
    elif method == "meta":
        time = datetime.fromisoformat(soup.find(tag, attrs={attr: attr_name})["content"]).strftime('%H:%M')
    else:
        print("get_time, no valid method selected.")
        sys.exit() 

    return time

def get_content(soup, method:str, tag:str, attr:str, attr_name:str, split:int):
    """universal method to retrieve content from tags, either single tag, multiple tag (use split) or meta tag"""
    if method == "tag":
        try:
            if split != -999:
                content = soup.find_all(tag, attrs={attr: attr_name})[int(split)].text.replace('\n', ' ').strip()
            else:
                content = soup.find(tag, attrs={attr: attr_name}).text.replace('\n', ' ').strip()
        except:
            return "event not found"
    elif method == "meta":
        try:
            content = soup.find("meta", attrs={attr: attr_name})[tag]
        except:
            return "event not found"
    else:
        print(f"{get_content.__name__}, no valid method selected.")
        sys.exit()
    return content

db_row = 0
#GATHER INFO ON ALL EVENTS AND SAVE THEM IN DATABASE (CSV)
for row in range(0, len(df)):
    events = get_all_events(link=str(df.iloc[row]['link']), container=df.iloc[row]['container'], search=str(df.iloc[row]['search']), type=str(df.iloc[row]['url_type']), method=str(df.iloc[row]['mode']))
    for count, event in enumerate(events):
        print(f"Processing event {count+1} of {len(events)}")
        response = requests.get(event, headers=headers)
        soup = BeautifulSoup(response.content, "html5lib")
        title = get_content(soup, method=str(df.iloc[row]['title_method']), tag=str(df.iloc[row]['title_tag']), attr=str(df.iloc[row]['title_attr']), attr_name=str(df.iloc[row]['title_attr_name']), split=int(df.iloc[row]['title_split']))
        start_date = get_date(soup, tag=str(df.iloc[row]['start_date_tag']), attr=str(df.iloc[row]['start_date_attr']), attr_name=str(df.iloc[row]['start_date_attr_name']), date_split=int(df.iloc[row]['start_date_split']), start_end_date_split=str(df.iloc[row]['start_end_date_split']), start_end=0)
        end_date = get_date(soup, tag=str(df.iloc[row]['end_date_tag']), attr=str(df.iloc[row]['end_date_attr']), attr_name=str(df.iloc[row]['end_date_attr_name']), date_split=int(df.iloc[row]['end_date_split']), start_end_date_split=str(df.iloc[row]['start_end_date_split']), start_end=1)
        #start_time = get_time(soup, method=str(df.iloc[row]['time_method']), tag=str(df.iloc[row]['time_tag']), attr=str(df.iloc[row]['time_attr']), attr_name=str(df.iloc[row]['time_attr_name']), time_split=int(df.iloc[row]['time_split']), start_end_time_split=str(df.iloc[row]['start_end_time_split']), start_end=0)
        #end_time = get_time(soup, method=str(df.iloc[row]['time_method']), tag=str(df.iloc[row]['time_tag']), attr=str(df.iloc[row]['time_attr']), attr_name=str(df.iloc[row]['time_attr_name']), time_split=int(df.iloc[row]['time_split']), start_end_time_split=str(df.iloc[row]['start_end_time_split']), start_end=1)
        address = get_content(soup, method=str(df.iloc[row]['address_method']), tag=str(df.iloc[row]['address_tag']), attr=str(df.iloc[row]['address_attr']), attr_name=str(df.iloc[row]['address_attr_name']), split=int(df.iloc[row]['address_split']))
        event_info = get_content(soup, method=str(df.iloc[row]['info_method']), tag=str(df.iloc[row]['info_tag']), attr=str(df.iloc[row]['info_attr']), attr_name=str(df.iloc[row]['info_attr_name']), split=int(df.iloc[row]['info_split']))
        #WRITE ALL EVENTS TO DATAFRAME
        df_out.loc[db_row] = [event, title, start_date, end_date, address,event_info]
        db_row +=1 
        #print(f"What: {title} When: {start_date} - {end_date} at: {address} info: {event_info}")

#SAVE DATAFRAME AS CSV
df_out.to_csv(df_out_path,index=False)