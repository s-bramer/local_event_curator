from bs4 import BeautifulSoup
from bs4.element import Comment
from calendar import month_name
from tabulate import tabulate
from datetime import date, datetime
import calendar
from date_muncher
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

def format_date(input_date_string:str, full_date_string:str):
    """convert date into proper date format"""
    if input_date_string == "":
        return "ERROR: invalid date string (empty)","n/a","n/a", full_date_string
    date_string = input_date_string.replace(',',' ')
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
        return f"ERROR: invalid date string (month not found): {input_date_string}","n/a","n/a", full_date_string
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
    #last check to see whether date fits format
    try:
        return_date = date(year=year,month=month,day=day).strftime('%a %d %b %Y')
        test_date = datetime.strptime(return_date,'%a %d %b %Y')
    except:
        return f"ERROR: invalid date string (format): {input_date_string}","n/a","n/a", full_date_string
    else:
        return_date = date(year=year,month=month,day=day)
        sorting_date = return_date.strftime('%Y-%m-%d')
        month_date = return_date.strftime('%B')
        return_date = return_date.strftime('%a %d %b')
        return return_date,month_date,sorting_date,full_date_string

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

def findElements(lst1, lst2):
    return list(np.array(lst1)[lst2])

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
    # print(start_end_date_split.split(','))
    if method == 'tag':
        try: 
            full_date = soup.find(tag, attrs={attr: attr_name}).text.replace('\n', ' ').strip()
        except:
            return "ERROR: date not found (tag)"
    elif method == 'tags':
        try: 
            full_date = soup.find_all(tag, attrs={attr: attr_name})[int(date_split)].text.replace('\n', ' ').strip()
        except:
            return "ERROR: date not found (tag)"
    else:
        print(f"{get_dates.__name__}, no valid method selected.")
        sys.exit()

    return full_date
    #         full_date = soup.find_all(tag, attrs={attr: attr_name})[int(date_split)].text.replace('\n', ' ').strip()
    #     else:
    #         full_date = soup.find(tag, attrs={attr: attr_name}).text.replace('\n', ' ').strip()
    #     try:
    #         if start_end_date_split != "-999":
    #             date_formatted = format_date(re.split(start_end_date_delimeters, full_date)[int(start_end)])
    #         else:
    #             date_formatted = format_date(full_date)
    #     except:
    #         return "","n/a","n/a",full_date_string
    # except:
    #     return "ERROR: event date not found (get date)","n/a","n/a",full_date_string
    # return date_formatted

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
            return "ERROR: event not found (tag_attr)"
    elif method == "tags_attr":
        try:
            content = ', '.join([str(item.text).strip() for item in soup.find_all(tag, attrs={attr: attr_name}) if tag_visible(item)])
        except:
            return "ERROR: event not found (tags_attr)"
    elif method == "tag":
        try:
            content = soup.find(tag).string.replace("’", "'")
        except:
            return "ERROR: event not found (tag)"
    elif method == "meta":
        try:
            content = soup.find("meta", attrs={attr: attr_name})[tag]
        except:
            return "ERROR: event not found (meta)"
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
    #df.drop_duplicates(subset="title",keep='first', inplace=True,ignore_index=True)
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
    df_out = pd.DataFrame(columns=['link', 'title', 'full_date', 'start_date', 'end_date', 'sort_date', 'month', 'location', 'location_search', 'info', 'name', 'favicon', 'root'])
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
                print(date_muncher(date_string, delimeters, connectors)) 

                title = get_content(soup, method=str(df_in.iloc[row]['title_method']), tag=str(df_in.iloc[row]['title_tag']), attr=str(df_in.iloc[row]['title_attr']), attr_name=str(df_in.iloc[row]['title_attr_name']), split=int(df_in.iloc[row]['title_split']))
                dates = get_dates(soup, tag=str(df_in.iloc[row]['start_date_tag']), attr=str(df_in.iloc[row]['start_date_attr']), attr_name=str(df_in.iloc[row]['start_date_attr_name']), date_split=int(df_in.iloc[row]['start_date_split']), start_end_date_split=str(df_in.iloc[row]['start_end_date_split']), start_end=0)
                start_date = start_dates[0]
                print(start_dates)
                full_date = start_dates[3]
            if not "ERROR:" in title and not "ERROR:" in start_date:
                end_dates = get_date(soup, tag=str(df_in.iloc[row]['end_date_tag']), attr=str(df_in.iloc[row]['end_date_attr']), attr_name=str(df_in.iloc[row]['end_date_attr_name']), date_split=int(df_in.iloc[row]['end_date_split']), start_end_date_split=str(df_in.iloc[row]['start_end_date_split']), start_end=1)
                if len(end_dates) > 0:
                    end_date = end_dates[0]
                month = start_dates[1]
                sort_date = start_dates[2]
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
                df_out.loc[db_out_row] = [event, titlecase(title), full_date, start_date, end_date, sort_date, month, address, location_search, event_info, name, favicon, root]
                db_out_row += 1
                # print(df_out)
                #!!!!!!REPORT OMITTED EVENTS!!!!!!!!
            else:
                df_out.loc[db_out_row] = [event, title, full_date, start_date, "", "", "", "", "", "", "", "", ""]
                db_out_row += 1
                continue
    else:
        pass
        # page not found items currently excluded - will be picked up by duplicate removal and cause error
        #df_out.loc[db_out_row] = [link, "page not found", "", "", "", "", "", "", "", "", "", "", ""]
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
    #df_out = event_post_processing(df_out)
    df_out.to_csv(df_out_path,index=False)