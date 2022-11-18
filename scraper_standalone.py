import date_muncher
from bs4 import BeautifulSoup
from bs4.element import Comment
from calendar import month_name
from tabulate import tabulate
from datetime import date, datetime
import numpy as np
import calendar
import requests
import pandas as pd
import re
import sys

# standard header for http request
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'}
# load event_pages CSV with links and search parameters
WEEKDAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']

last_month = "" #for month column, outlining month blocks

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

# def format_time(time_string):
#     return_time = datetime.strptime(time_string.strip(),"%H:%M")
#     return return_time.strftime('%H:%M')

def get_all_events(link: str,  container: str, container_attr: str, search: str, root: str, type="absolute", method="search"):
    """Returns all events urls from a webpage"""
    if method == 'none': 
        return "ERROR: page not found (get_all_events: none)" 
    all_events = []
    try:
        response = requests.get(link, headers=headers, timeout =10)
        soup = BeautifulSoup(response.content, "html5lib")
    except:
        return "ERROR: page not found (get_all_events)"
    else:
        # if container passed step into it
        if not pd.isna(container):
            soup = soup.find("div", attrs={container_attr: container})
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
            all_events = [link + event for event in all_events]
        if type =="relative_root":
            all_events = [root + event for event in all_events]

        return all_events

############
# GET DATE #
############
def get_dates(soup, method:str, tag:str, attr:str, attr_name:str, date_indices:str, date_delimiter:int, date_connector:str):
    """extract the event date from event page"""
    indices = date_indices.split(',')
    if method == 'tag':
        try: 
            full_date = soup.find(tag, attrs={attr: attr_name}).text.replace('\n', ' ').strip()
        except:
            return "ERROR: date not found (tag)","n/a","n/a","n/a"
    elif method == 'tags':
        try: 
            full_date = ""
            for indicy in indices:
                full_date = full_date + soup.find_all(tag, attrs={attr: attr_name})[int(indicy)].text
        except:
            return "ERROR: date not found (tags)","n/a","n/a","n/a"
    else:
        print(f"{get_dates.__name__}, no valid method selected.")
        sys.exit()
    
    return_dates = date_muncher.munch_munch(full_date,date_delimiter,date_connector)

    return return_dates

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
            return "ERROR: content not found (tag_attr)"
    elif method == "tags_attr":
        try:
            content = ', '.join([str(item.text).strip() for item in soup.find_all(tag, attrs={attr: attr_name}) if tag_visible(item)])
        except:
            return "ERROR: content not found (tags_attr)"
    elif method == "tag":
        try:
            content = soup.find(tag).string.replace("’", "'")
        except:
            return "ERROR: content not found (tag)"
    elif method == "meta":
        try:
            content = soup.find("meta", attrs={attr: attr_name})[tag]
        except:
            return "ERROR: content not found (meta)"
    else:
        print(f"{get_content.__name__}, no valid method selected.")
        sys.exit()
    return content

def event_post_processing(df:pd.DataFrame):
    """sorting, removing duplicates, removing events with certain strings"""
    dicard_list = ['Cancelled', 'Luminatae']
    df = df.sort_values(by='sort_date',ascending=True,ignore_index=True)
    #add max_date column to get the maximum date of duplicate events (used for end date)
    df['max_date'] = df.groupby(['title'])['sort_date'].transform(max)
    #add dupl_count column to identify duplicate rows
    df['dupl_count'] = df.groupby(['title'])['sort_date'].transform('size')
    #remove title duplicates and keep first date (min = start date)
    #df.drop_duplicates(subset=['title','location'],keep='first', inplace=True,ignore_index=True)
    current_month = ""
    for row in range(0, len(df)):
        #if duplicate use max_date as end_date
        if df.loc[row, ('dupl_count')] > 1:
            df.loc[row, ('end_date')] = datetime.strptime(df.loc[row, ('max_date')],'%Y-%m-%d').strftime('%a %d %b')
        #remove month duplicates (for month subsection labels)
        if df.loc[row, ('month')] != current_month:
            current_month = df.loc[row, ('month')]
        else:
            #print(f"{df_out_out.loc[row, ('title')]} month {df_out_out.loc[row, ('month')]} deleted from row {row}")
            df.loc[row, ('month')] = ""    
    
    #remove row containing keywords
    df = df[df["title"].str.contains('|'.join(dicard_list)) == False]
    #df = df.drop(['max_date', 'dupl_count'], axis=1)
    df['update_date'] = datetime.now().strftime('%d %b %Y %H:%M')
    return df

def run_scraper(link, row, df_in): 
    """main function, runs scraper and returns events CSV"""
    #GATHER INFO ON ALL EVENTS AND SAVE THEM IN DATABASE (CSV)
    db_out_row = 0 #row in output df
    df_out = pd.DataFrame(columns=['link', 'title', 'full_date', 'print_date', 'sort_date', 'month', 'location', 'location_search', 'info', 'name', 'favicon', 'root'])
    events = get_all_events(link, container=df_in.iloc[row]['container'], container_attr=df_in.iloc[row]['container_attr'], search=str(df_in.iloc[row]['search']), root=str(df_in.iloc[row]['root']), type=str(df_in.iloc[row]['url_type']), method=str(df_in.iloc[row]['mode']))
    if not "ERROR:" in events:
        for count, event in enumerate(events):
            print(f"Processing event {count+1} of {len(events)} ({event})")
            #get the individual event pages
            try:
                response = requests.get(event, headers=headers, timeout =10)
                soup = BeautifulSoup(response.content, "html5lib")
            except:
                title == "ERROR: event not found"
            else:
                title = get_content(soup, method=str(df_in.iloc[row]['title_method']), tag=str(df_in.iloc[row]['title_tag']), attr=str(df_in.iloc[row]['title_attr']), attr_name=str(df_in.iloc[row]['title_attr_name']), split=int(df_in.iloc[row]['title_split']))
                dates = get_dates(soup, method=str(df_in.iloc[row]['date_method']), tag=str(df_in.iloc[row]['date_tag']), attr=str(df_in.iloc[row]['date_attr']), attr_name=str(df_in.iloc[row]['date_attr_name']), date_indices=str(df_in.iloc[row]['date_indices']), date_delimiter=str(df_in.iloc[row]['date_delimiters']), date_connector=str(df_in.iloc[row]['date_connectors']))
                #print(dates)
                full_date = dates[0]
                print_date = dates[1]
                sort_date = dates[2]
                month = dates[3]
                if str(df_in.iloc[row]['address']) == 'no':
                    address = get_content(soup, method=str(df_in.iloc[row]['address_method']), tag=str(df_in.iloc[row]['address_tag']), attr=str(df_in.iloc[row]['address_attr']), attr_name=str(df_in.iloc[row]['address_attr_name']), split=int(df_in.iloc[row]['address_split']))
                else:
                    address = df_in.iloc[row]['address']
                location_search = ' '.join(address.split(','))
                event_info = get_content(soup, method=str(df_in.iloc[row]['info_method']), tag=str(df_in.iloc[row]['info_tag']), attr=str(df_in.iloc[row]['info_attr']), attr_name=str(df_in.iloc[row]['info_attr_name']), split=int(df_in.iloc[row]['info_split']))
                name = str(df_in.iloc[row]['name'])
                favicon = str(df_in.iloc[row]['favicon'])
                root = str(df_in.iloc[row]['root'])
                #WRITE ALL EVENTS TO DATAFRAME
                df_out.loc[db_out_row] = [event, titlecase(title), full_date, print_date, sort_date, month, address, location_search, event_info, name, favicon, root]
                db_out_row += 1
                # print(df_out)
                #!!!!!!REPORT OMITTED EVENTS!!!!!!!!
    else:
        pass
        # page not found items currently excluded - will be picked up by duplicate removal and cause error
        #df_out.loc[db_out_row] = [link, "page not found", "", "", "", "", "", "", "", "", "", "", ""]
        #db_out_row += 1

    return df_out

if __name__ == '__main__':
    # event_pages_data = "event_pages.csv"
    # df_in = pd.read_csv(event_pages_data, header=0, index_col=None)
    df_out_path = "events_database_pp.csv"
    # df_out = pd.DataFrame()
    # for i, row in enumerate(range(0, len(df_in))):
    #     link = str(df_in.iloc[row]['link'])
    #     df_out = pd.concat(objs=[df_out, run_scraper(link, row, df_in)])

    # Post-process and save dataframe
    df_out = pd.read_csv("events_database.csv", header=0, index_col=None)
    df_out = event_post_processing(df_out)
    df_out.to_csv(df_out_path,index=False)