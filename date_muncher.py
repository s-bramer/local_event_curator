import re
import pandas as pd
import time
import calendar
from datetime import date, datetime

ORDINALS = ['th', 'st', 'nd', 'rd', 'TH', 'ST', 'ND', 'RD']
THIS_YEAR = date.today().year


def is_timestamp(text: str):
    """check if string is time stamp"""
    text = text.strip()
    if 'am' in text or 'pm' in text or 'GMT' in text:
        return True
    else:
        try:
            time.strptime(text, '%H:%M')
        except ValueError:
            try:
                time.strptime(text, '%H.%M')
            except ValueError:
                return False
            else:
                return True
        else:
            return True

def is_day_name(text: str):
    """check if string is a day name (e.g. Monday, Mon,.."""
    return text in list(calendar.day_name[1:]) or text in list(calendar.day_abbr[1:])

def is_datetime(text:str):
    """check if string is datetime"""
    try:
        date_time = datetime.strptime(text, '%d/%m/%Y')
    except ValueError:
        try:
            date_time = datetime.strptime(text, '%d.%m.%Y')
        except ValueError:
            return "not a date"
        else:
            return date_time
    else:
        return date_time


def is_day(text: str):
    """check if string is day"""
    text = text.strip()
    try:
        day_number = int(text)
    except ValueError:
        return False
    else:
        return 1 <= day_number <= 31

def is_month(text: str):
    """check if string is month"""
    return text in list(calendar.month_name[1:]) or text in list(calendar.month_abbr[1:])

def is_year(text: str):
    """check if string is year"""
    text = text.strip()
    try:
        year_number = int(text)
    except:
        return False
    else:
        return 1900 <= year_number <= 3000

def count_string(text:str, connectors:str, delimiters:str):
    """count the strings in text"""
    text = text.strip()
    str_counter = 0
    for char in text.split():
        if is_day(char) or is_month(char) or is_year(char) or is_timestamp(char) or char in connectors or char in delimiters:
            pass
        else:
            if isinstance(char,str):
                str_counter +=1
    return str_counter
    
def munch_munch(date_string, delims: str, conns: str):
    comment_string_found = False
    if date_string == "":
        return date_string, "No date found, please see event details.", 'date not found', 'date not found', 'date not found'
    else:
        delimiters = '|'.join(delims.split(';'))
        connectors = conns.split(';')
        # break components of string into list/keep the delimeters
        # date_string = date_string.replace(' ',',')
        date_list = re.split(f"({(delimiters)})", date_string)
        days, months, years, conns = [], [], [], []
        dummy = ""
        # walk through the items identifying each one
        for index, item in enumerate(date_list):
            #check if this is a text string > 2 strings i.e. end date comment = remove all other items
            if count_string(item,delimiters,connectors) > 2:
                comment_string_found = True
            if comment_string_found:
                #print(f"remove: {item}")
                date_list.pop(index)
            # check if weekday name (full or abbr) - remove it
            elif is_day_name(item):
                date_list.pop(index)
            elif is_timestamp(item):
                #print(f"time found: {item}")
                date_list.pop(index)
            else:
                for char in item.split():
                    char = char.strip()
                    # remove ordinals
                    if any(ordinal in char[-2:] for ordinal in ORDINALS) and not is_month(char) and not is_day_name(char):
                        for ordinal in ORDINALS:
                            char = char.replace(ordinal, "")
                    if is_day(char):
                        #print(f"day found: {char}")
                        days.append(int(char))
                        dummy += char
                    elif is_month(char):
                        #print(f"month found: {char}")
                        if len(char) == 3:
                            month = list(calendar.month_abbr).index(char)
                        else:
                            month = list(calendar.month_name).index(char)
                        months.append(month)
                        dummy += ' ' + calendar.month_abbr[month]
                    elif is_year(char):
                        #print(f"year found: {char}")
                        years.append(int(char))
                        if int(THIS_YEAR) != int(char):
                            dummy += ' ' + char
                    elif char in connectors:
                        #print(f"conn found: {char}")
                        conns.append(char)
                        dummy += ' ' + char + ' '
                    elif char in delimiters:
                        #print(f"deli found: {char}")
                        dummy += char + ' '
                    else:
                        if is_datetime(char) != "not a date":
                            # last attempt, perhaps its already in date time format
                            date_time = is_datetime(char)
                            days.append(date_time.day)
                            months.append(date_time.month)
                            years.append(date_time.year)
        # catch meaning less datestrings (e.g. First Thursday of each month)
        if len(days) == 0 or len(months) == 0:
            return date_string, "No date found, please see event details.", 'date not found', 'date not found', 'date not found'
        # remove trailing delimiter
        dummy = dummy.rstrip()
        try:
            if dummy[-1] in delimiters:
                dummy = dummy[:-1]
        except IndexError:
            pass
        # build the start date, end date, sort date and month
        # 4 cases:
        # 1. empty date_string - handle on top
        # 2. one day = single date
        # 3. two days = start and end date (keep delimeter - or &)
        # 4. more than two days, print it as is (you got the sort date and the month)
        if len(years) == 0:
            years.append(THIS_YEAR)
        dump_date = date(year=years[0], month=months[0], day=days[0])
        sorting_date = dump_date.strftime('%Y-%m-%d')
        if THIS_YEAR != dump_date.year:
            month_date = dump_date.strftime('%B %Y')
            print_date = dump_date.strftime('%a %d %b %Y')
        else:
            month_date = dump_date.strftime('%B')
            print_date = dump_date.strftime('%a %d %b')
        # if len(days) == 2 and days[0] != days[1]:
        if len(days) == 2:
            if len(months) == 1:
                months.append(months[0])
            if len(years) == 1:
                years.append(years[0])
            if len(conns) == 0:
                conns.append('-')
            dump_date = date(year=years[1], month=months[1], day=days[1])
            if THIS_YEAR != dump_date.year:
                second_date = dump_date.strftime('%a %d %b %Y')
            else:
                second_date = dump_date.strftime('%a %d %b')
            #combine start and end date, check that both dates are not the same (some pages print 2 dates although they are the same)
            if print_date != second_date:
                print_date = f"{print_date} {conns[0]} {second_date}"
        if len(days) > 2:
            print_date = dummy
        end_date = date(year=years[-1], month=months[-1],
                        day=days[-1]).strftime('%Y-%m-%d')
        return date_string, print_date, sorting_date, month_date, end_date

# if __name__ == '__main__':
#     date_string = "01                         Dec                         2022                         -                         01                         Jan                         2023"
#     #date_string = "15                         Nov                         2022                         -                         08                         Jan                         2023"
#     date_string ="3–22 December 2022, 2pm-5pm"
#     delims = "–;,"
#     conns = "–;-;&;+"
#     print(munch_munch(date_string, delims, conns))
#     print(is_datetime("04.02.2023"))
#     print(count_string("2 February"))
