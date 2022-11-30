import date_muncher
import address_sniffer
from bs4 import BeautifulSoup
from bs4.element import Comment
from datetime import date, datetime
import numpy as np
import requests
import pandas as pd
import re
import sys

# standard header for http request
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'}
# load event_pages CSV with links and search parameters
CATEGORIES = ['event', 'digital_event', 'course', 'exhibition', 'performance']

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
            try:
                for tag in soup.find_all(href=re.compile(search)):
                    all_events.append(tag.get('href'))
            except:
                return "ERROR: page not found (get_all_events)"
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

def get_dates(soup, method:str, tag:str, attr:str, attr_name:str, date_indices:str, date_delimiter:int, date_connector:str):
    """extract the event date from event page"""
    indices = date_indices.split(',')
    if method == 'tag_attr':
        try: 
            full_date = soup.find(tag, attrs={attr: attr_name}).text.replace('\n', ' ').strip()
        except:
            return "ERROR: date not found (tag)","date not found","date not found","date not found",'date not found'
    elif method == 'tags_attr':
        try: 
            full_date = ""
            for indicy in indices:
                full_date = full_date + soup.find_all(tag, attrs={attr: attr_name})[int(indicy)].text
        except:
            return "ERROR: date not found (tags)","date not found","date not found","date not found",'date not found'
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
                content = soup.find_all(tag, attrs={attr: attr_name})[int(split)].text
            else:
                content = soup.find(tag, attrs={attr: attr_name}).text
        except:
            return "ERROR: content not found (tag_attr)"
    elif method == "tags_attr":
        try:
            content = ', '.join([str(item.text).strip() for item in soup.find_all(tag, attrs={attr: attr_name}) if tag_visible(item)])
        except:
            return "ERROR: content not found (tags_attr)"
    elif method == "tag":
        try:
            #print(soup.find(tag))
            content = soup.find(tag).string
        except:
            return "ERROR: content not found (tag)"
    elif method == "tags":
        try:
            #print(soup.find(tag))
            content = soup.find_all(tag)[int(split)].string
        except:
            return "ERROR: content not found (tags)"
    elif method == "meta":
        try:
            content = soup.find("meta", attrs={attr: attr_name})[tag]
        except:
            return "ERROR: content not found (meta)"
    else:
        print(f"{get_content.__name__}, no valid method selected.")
        sys.exit()
    return content.replace('\n', ' ').replace("’", "'").strip()

def get_category(soup, method:str, tag:str, attr:str, attr_name:str, split:int):
    """find category of event (for filter)"""
    if method == "direct":
        try:
            if split != -999:
                category = soup.find_all(tag, attrs={attr: attr_name})[int(split)].text
            else:
                category = soup.find(tag, attrs={attr: attr_name}).text
        except:
            return "ERROR: category not found (direct)"
        else:
            #remove trailing : from AC categories, formatting
            category = category.strip().lower()
            if category[-1] == ':':
                category = category[:-1]
            category = category.replace(' ','_')
    elif method == "search":
        try:
            if split != -999:
                content = soup.find_all(tag, attrs={attr: attr_name})[int(split)].text
            else:
                content = soup.find(tag, attrs={attr: attr_name}).text
        except:
            return "ERROR: category not found (search)"
        else:
            exhi_list = ['exhibition', 'exhibited']
            class_list = ['workshop', 'course', 'craft']
            if any(item in content[0:100].lower() for item in exhi_list):
                category = 'exhibition'
            elif any(item in content[0:100].lower() for item in class_list):
                category = 'course'
            else:
                category = 'event'
    elif method == "single":
        category = tag
    else:
        print(f"{get_category.__name__}, no valid method selected.")
        sys.exit()
    if category not in CATEGORIES:
        category = 'event'

    return category

def event_post_processing(df:pd.DataFrame):
    """sorting, removing duplicates, removing events with certain strings"""
    dicard_list_title = ['Cancelled', 'Luminatae']
    discard_list_location = ['Fully\sBooked']
    #remove rows containing keywords
    df = df[df["title"].str.contains('|'.join(dicard_list_title)) == False]
    df = df[df["location"].str.contains('|'.join(discard_list_location)) == False]
    df = df.sort_values(by='sort_date',ascending=True,ignore_index=True)
    #remove row with end_date > today (expired)
    df = df.loc[(df['end_date'] >= date.today().strftime('%Y-%m-%d'))]
    #add max_date column to get the maximum date of duplicate events (used for end date)
    df['max_date'] = df.groupby(['title'])['sort_date'].transform(max)
    #add dupl_count column to identify duplicate rows
    df['dupl_count'] = df.groupby(['title','location'])['sort_date'].transform('size')
    #remove title duplicates and keep first date (min = start date)
    df.drop_duplicates(subset=['title','location'],keep='first', inplace=True,ignore_index=True)
    #add column for relative day count (past, present,future)
    df["ppf"] = ""
    current_month = ""
    #df.loc[0, ('month')] = "Today"
    for row in range(0, len(df)):
        #if duplicate row, use max_date as end_date (if its different to start date)
        if df.loc[row, ('dupl_count')] > 1 and df.loc[row, ('sort_date')] != df.loc[row, ('max_date')]:
            df.loc[row, ('print_date')] = df.loc[row, ('print_date')] + ' - ' + datetime.strptime(df.loc[row, ('max_date')],'%Y-%m-%d').strftime('%a %d %b')
        #identify todays, future and past events (to be omitted)
        if df.loc[row, ('sort_date')] != 'date not found':
            sort_time = datetime.strptime(df.loc[row, ('sort_date')], '%Y-%m-%d')
            df.loc[row, ('ppf')] = (date(sort_time.year, sort_time.month, sort_time.day) - date(datetime.now().year, datetime.now().month, datetime.now().day)).days
        else:
            df.loc[row, ('ppf')] = '999'
        #remove month duplicates (for month subsection labels) omit current month
        if df.loc[row, ('month')] != current_month and int(df.loc[row, ('ppf')]) > 0 and df.loc[row, ('month')] != date.today().strftime('%B'):
            current_month = df.loc[row, ('month')]
        else:
            #print(f"{df_out_out.loc[row, ('title')]} month {df_out_out.loc[row, ('month')]} deleted from row {row}")
            df.loc[row, ('month')] = ""
    
    #df = df.drop(['max_date', 'dupl_count'], axis=1)
    df['update_date'] = datetime.now().strftime('%d %b %Y %H:%M')
    return df

def run_scraper(link, row, df_in): 
    """main function, runs scraper and returns events CSV"""
    #GATHER INFO ON ALL EVENTS AND SAVE THEM IN DATABASE (CSV)
    db_out_row = 0 #row in output df
    title = ""
    df_out = pd.DataFrame(columns=['link', 'title', 'full_date', 'print_date', 'date_info', 'sort_date', 'end_date', 'month', 'location', 'short_location', 'postcode', 'council', 'council_abbr', 'location_search', 'category', 'info', 'name', 'logo', 'root', 'event_icon'])
    events = get_all_events(link, container=df_in.iloc[row]['events_container'], container_attr=df_in.iloc[row]['events_container_attr'], search=str(df_in.iloc[row]['events_search']), root=str(df_in.iloc[row]['root']), type=str(df_in.iloc[row]['events_url_type']), method=str(df_in.iloc[row]['events_mode']))
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
                title = titlecase(title)
                #['Uwc','Bbc','Swam'] ['UWC','BBC','SWAM']
                title = title.replace('Bbc','BBC')
                title = title.replace('Swam', 'SWAM')
                title = title.replace('Uwc', 'UWC')
                title = title.replace('Lgbtq','LGBTQ')
                dates = get_dates(soup, method=str(df_in.iloc[row]['date_method']), tag=str(df_in.iloc[row]['date_tag']), attr=str(df_in.iloc[row]['date_attr']), attr_name=str(df_in.iloc[row]['date_attr_name']), date_indices=str(df_in.iloc[row]['date_indices']), date_delimiter=str(df_in.iloc[row]['date_delimiters']), date_connector=str(df_in.iloc[row]['date_connectors']))
                date_info = df_in.iloc[row]['date_info']
                full_date = dates[0]
                print_date = dates[1]
                if not pd.isna(date_info):
                    print_date = print_date + " *"
                sort_date = dates[2]
                month = dates[3]
                end_date = dates [4]
                #LOCATION/ADDRESS
                if str(df_in.iloc[row]['address']) == 'no':
                    location = get_content(soup, method=str(df_in.iloc[row]['address_method']), tag=str(df_in.iloc[row]['address_tag']), attr=str(df_in.iloc[row]['address_attr']), attr_name=str(df_in.iloc[row]['address_attr_name']), split=int(df_in.iloc[row]['address_split']))
                else:
                    location = df_in.iloc[row]['address']
                if location == "":
                    location = get_content(soup, method=str(df_in.iloc[row]['alt_address_method']), tag=str(df_in.iloc[row]['alt_address_tag']), attr=str(df_in.iloc[row]['alt_address_attr']), attr_name=str(df_in.iloc[row]['alt_address_attr_name']), split=int(df_in.iloc[row]['alt_address_split']))
                if location[-1] == ':':
                    location = location[:-1]
                location_search = ' '.join(location.split(','))
                postcode = address_sniffer.get_postcode(location)
                councils = address_sniffer.get_council(postcode)
                short_location = address_sniffer.get_town(postcode)
                if short_location.lower() == "castle":
                    short_location = councils[0]
                council = councils[0]
                council_abbr = councils[1] 
                #EVENT CATEGORY
                category = get_category(soup, method=str(df_in.iloc[row]['cat_method']), tag=str(df_in.iloc[row]['cat_tag']), attr=str(df_in.iloc[row]['cat_attr']), attr_name=str(df_in.iloc[row]['cat_attr_name']), split=int(df_in.iloc[row]['cat_split']))
                #EVENT INFO
                event_info = get_content(soup, method=str(df_in.iloc[row]['info_method']), tag=str(df_in.iloc[row]['info_tag']), attr=str(df_in.iloc[row]['info_attr']), attr_name=str(df_in.iloc[row]['info_attr_name']), split=int(df_in.iloc[row]['info_split']))
                if len(event_info) > 500:
                    event_info = event_info[:500] + '...'
                remove_list = ['[',']',' email protected']
                for item in remove_list:
                    if item in event_info:
                        print (f"item {item} removed..")
                    event_info = event_info.replace(item,"")

                #ADDITIONAL INFO
                name = str(df_in.iloc[row]['name'])
                logo = str(df_in.iloc[row]['logo'])
                #event_icon = f"./static/images/{category}.png"
                event_icon = logo
                root = str(df_in.iloc[row]['root'])
                #WRITE ALL EVENTS TO DATAFRAME
                df_out.loc[db_out_row] = [event, title, full_date, print_date, date_info, sort_date, end_date , month, location, short_location, postcode, council, council_abbr, location_search, category, event_info, name, logo, root, event_icon]
                db_out_row += 1
                # print(df_out)
                #!!!!!!REPORT OMITTED EVENTS!!!!!!!!
    else:
        print(f"page not found: {link}")
        # page not found items currently excluded - will be picked up by duplicate removal and cause error
        #df_out.loc[db_out_row] = [link, "page not found", "", "", "", "", "", "", "", "", "", "", "", "", ""]
        #db_out_row += 1

    return df_out

if __name__ == '__main__':
    event_pages_data = "event_pages.csv"
    df_in = pd.read_csv(event_pages_data, header=0, index_col=None)
    df_out_path = "events_database.csv"
    df_out = pd.DataFrame()
    for i, row in enumerate(range(0, len(df_in))):
        link = str(df_in.iloc[row]['link'])
        df_out = pd.concat(objs=[df_out, run_scraper(link, row, df_in)])

    # Post-process and save dataframe
    #df_out = pd.read_csv("events_database.csv", header=0, index_col=None)
    df_out = event_post_processing(df_out)
    df_out.to_csv(df_out_path,index=False)