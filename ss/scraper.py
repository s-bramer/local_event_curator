from bs4 import BeautifulSoup
from bs4.element import Comment
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
    return return_date.strftime('%a %d %b %Y')

def tag_visible(element):
    """checks whether text is visible"""
    if element.parent.name in ['div','style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def titlecase(s):
    """proper casing for the event description"""
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda word: word.group(0).capitalize(),s)

def format_time(time_string):
    return_time = datetime.strptime(time_string.strip(),"%H:%M")
    return return_time.strftime('%H:%M')

def get_all_events(link: str,  container: str, search: str, type="absolute", method="search"):
    """Returns all events urls from a webpage"""
    all_events = []
    try:
        response = requests.get(link, headers=headers, timeout =10)
        soup = BeautifulSoup(response.content, "html5lib")
    except:
        return "page not found"
    else:
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
    """extract the event date from event page"""
    try:
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
    except:
        return "event date not found"
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
    if method == "tag_attr":
        try:
            if split != -999:
                content = soup.find_all(tag, attrs={attr: attr_name})[int(split)].text.replace('\n', ' ').replace("’", "'").strip()
            else:
                content = soup.find(tag, attrs={attr: attr_name}).text.replace('\n', ' ').replace("’", "'").strip()
        except:
            return ""
    elif method == "tags_attr":
        try:
            content = ', '.join([str(item.text).strip() for item in soup.find_all(tag, attrs={attr: attr_name}) if tag_visible(item)])
        except:
            return "event not found"
    elif method == "tag":
        try:
            content = soup.find(tag).string.replace("’", "'")
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

def run_scraper(event_page_link:str):
    """main function, runs scraper and returns events CSV"""
    df = pd.read_csv(event_page_link, header=0, index_col=None)
    df_out = pd.DataFrame(columns=['link', 'title', 'start_date', 'end_date', 'sort_date', 'month', 'location', 'location_search', 'info', 'name', 'favicon', 'root'])
    df_out_path = r"events_database.csv"
    db_row = 0 #row in output df
    last_month = "" #for month column, outlining month blocks
    #GATHER INFO ON ALL EVENTS AND SAVE THEM IN DATABASE (CSV)
    for row in range(0, len(df)):
        link = str(df.iloc[row]['link'])
        events = get_all_events(link, container=df.iloc[row]['container'], search=str(df.iloc[row]['search']), type=str(df.iloc[row]['url_type']), method=str(df.iloc[row]['mode']))
        if events != "page not found":
            for count, event in enumerate(events):
                print(f"Processing event {count+1} of {len(events)}")
                #get the individual event pages
                try:
                    response = requests.get(event, headers=headers, timeout =10)
                    soup = BeautifulSoup(response.content, "html5lib")
                except:
                    title == "event not found"
                else:    
                    title = get_content(soup, method=str(df.iloc[row]['title_method']), tag=str(df.iloc[row]['title_tag']), attr=str(df.iloc[row]['title_attr']), attr_name=str(df.iloc[row]['title_attr_name']), split=int(df.iloc[row]['title_split']))
                    start_date = get_date(soup, tag=str(df.iloc[row]['start_date_tag']), attr=str(df.iloc[row]['start_date_attr']), attr_name=str(df.iloc[row]['start_date_attr_name']), date_split=int(df.iloc[row]['start_date_split']), start_end_date_split=str(df.iloc[row]['start_end_date_split']), start_end=0)
                
                if title != "event not found" and start_date != "event date not found":
                    end_date = get_date(soup, tag=str(df.iloc[row]['end_date_tag']), attr=str(df.iloc[row]['end_date_attr']), attr_name=str(df.iloc[row]['end_date_attr_name']), date_split=int(df.iloc[row]['end_date_split']), start_end_date_split=str(df.iloc[row]['start_end_date_split']), start_end=1)
                    sort_date = datetime.strptime(start_date,'%a %d %b %Y').strftime('%Y-%m-%d')
                    month = datetime.strptime(start_date,'%a %d %b %Y').strftime('%B' )
                    start_date = datetime.strptime(start_date,'%a %d %b %Y').strftime('%a %d %b')
                    if end_date != "":
                        end_date = datetime.strptime(end_date,'%a %d %b %Y').strftime('%a %d %b')
                    #start_time = get_time(soup, method=str(df.iloc[row]['time_method']), tag=str(df.iloc[row]['time_tag']), attr=str(df.iloc[row]['time_attr']), attr_name=str(df.iloc[row]['time_attr_name']), time_split=int(df.iloc[row]['time_split']), start_end_time_split=str(df.iloc[row]['start_end_time_split']), start_end=0)
                    #end_time = get_time(soup, method=str(df.iloc[row]['time_method ])  tag=str(df.iloc[row]['time_tag']), attr=str(df.iloc[row]['time_attr']), attr_name=str(df.iloc[row]['time_attr_name']), time_split=int(df.iloc[row]['time_split']), start_end_time_split=str(df.iloc[row]['start_end_time_split']), start_end=1)
                    address = get_content(soup, method=str(df.iloc[row]['address_method']), tag=str(df.iloc[row]['address_tag']), attr=str(df.iloc[row]['address_attr']), attr_name=str(df.iloc[row]['address_attr_name']), split=int(df.iloc[row]['address_split']))
                    location_search = ' '.join(address.split(','))
                    event_info = get_content(soup, method=str(df.iloc[row]['info_method']), tag=str(df.iloc[row]['info_tag']), attr=str(df.iloc[row]['info_attr']), attr_name=str(df.iloc[row]['info_attr_name']), split=int(df.iloc[row]['info_split']))
                    name = str(df.iloc[row]['name'])
                    favicon = str(df.iloc[row]['favicon'])
                    root = str(df.iloc[row]['root'])
                    #WRITE ALL EVENTS TO DATAFRAME
                    df_out.loc[db_row] = [event, titlecase(title), start_date, end_date, sort_date, month, address, location_search, event_info, name, favicon, root]
                    db_row +=1
                    #!!!!!!REPORT OMITTED EVENTS!!!!!!!!
                else:
                    df_out.loc[db_row] = [event, title, start_date, "", "", "", "", "", "", "", "", ""]
                    db_row +=1
                    continue
        else:
            df_out.loc[db_row] = [link, "page not found", "", "", "", "", "", "", "", "", "", ""]
            db_row +=1

    #SAVE DATAFRAME AS CSV
    #first sort by sort_date
    df_out = df_out.sort_values(by='sort_date',ascending=True,ignore_index=True)
    #then remove month duplicates (for month subsection labels)
    current_month = ""
    for row in range(0, len(df_out)):
        if df_out.loc[row, ('month')] != current_month:
            current_month = df_out.loc[row, ('month')]
        else:
            #print(f"{df_out.loc[row, ('title')]} month {df_out.loc[row, ('month')]} deleted from row {row}")
            df_out.loc[row, ('month')] = ""
    df_out.to_csv(df_out_path,index=False)

if __name__ == '__main__':
    run_scraper("event_pages.csv")
