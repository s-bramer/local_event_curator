#THIS FILE IS JUST FOR TESTING CODE#
#DELETE ME!!#
import re
import pandas as pd
import time
import calendar
from datetime import date, datetime

def is_timestamp(text:str):
    """check if text is time stamp"""
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
           
def is_day(text:str):
    """check if text is day"""
    text = text.strip()
    try:
        day_number = int(text)
    except:
        return False
    else:
        return 1 <= day_number <= 31

def is_year(text:str):
    """check if string is year"""
    text = text.strip()
    try:
        year_number = int(text)
    except:
        return False
    else:
        return 1900 <= year_number <= 3000

def munch_munch(date_string, delims:str, conns:str):
    if date_string == "":
        return date_string, "No date found, please see event details.",'n/a','n/a'
    else:
        delimiters = '|'.join(delims.split(';'))
        connectors = conns.split(';')
        #break components of string into list/keep the delimeters
        # date_string = date_string.replace(' ',',')
        date_list = re.split(f"({(delimiters)})", date_string)
        days, months, years, conns = [],[],[],[]
        dummy = ""
        #walk through the items identifying each one
        for index, item in enumerate(date_list):
            #print(item)
            #check if weekday (full or abbr) - remove it
            if item in list(calendar.day_name[1:]) or item in list(calendar.day_abbr[1:]):
                date_list.pop(index)
            elif is_timestamp(item):
                #print(f"time found: {item}")
                date_list.pop(index)
            else:
                for char in item.split():
                    char = char.strip()
                    if is_day(char):
                        #print(f"day found: {char}")
                        days.append(int(char))
                        dummy += char
                    elif char in list(calendar.month_name[1:]) or char in list(calendar.month_abbr[1:]):
                        if len(char) == 3:
                            month = list(calendar.month_abbr).index(char)
                        else:
                            month = list(calendar.month_name).index(char)
                        months.append(month)
                        dummy += ' ' + calendar.month_abbr[month]
                    elif is_year(char):
                        #print(f"year found: {char}")
                        years.append(int(char))
                    elif char in connectors:
                        #print(f"conn found: {char}")
                        conns.append(char)
                        dummy += ' '+ char + ' '
                    elif char in delimiters:
                        #print(f"deli found: {char}")
                        dummy += char+ ' '
                    else:
                        pass
        #catch meaning less datestrings (e.g. First Thursday of each month)
        if len(days) == 0 or len(months)==0:
            return date_string, "No date found, please see event details.",'n/a','n/a'
        #remove trailing delimiter
        dummy = dummy.rstrip()
        if dummy[-1] in delimiters:
            dummy = dummy[:-1]

        #build the start date, end date, sort date and month
        #4 cases:
        #1. empty date_string - handle on top
        #2. one day = single date
        #3. two days = start and end date (keep delimeter - or &)
        #4. more than two days, print it as is (you got the sort date and the month)
        if len(years) == 0:
            years.append(date.today().year)
        dump_date = date(year=years[0],month=months[0],day=days[0])
        sorting_date = dump_date.strftime('%Y-%m-%d')
        month_date = dump_date.strftime('%B')
        print_date = dump_date.strftime('%a %d %b')
        if len(days) == 2:
            if len(months)==1:
                months.append(months[0])
            if len(years) == 1:
                years.append(years[0])
            if len(conns)==0:
                conns.append('-')
            dump_date = date(year=years[1],month=months[1],day=days[1])     
            print_date = f"{print_date} {conns[0]} {dump_date.strftime('%a %d %b')}"
        if len(days) > 2:
            print_date = dummy  
        return date_string, print_date, sorting_date, month_date


if __name__ == '__main__':
    ds = "3 & 4 December 2022, 10am - 5pm"
    print(munch_munch(ds,'–;&;,','–;& '))
