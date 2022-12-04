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


def munch_munch(date_string, delims: str, conns: str):
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
            # check if weekday name (full or abbr) - remove it
            if is_day_name(item):
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
                        try:
                            # last attempt, perhaps its already in date time format
                            date_time = datetime.strptime(char, '%d/%m/%y')
                        except:
                            pass
                        else:
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
        if len(days) == 2 and days[0] != days[1]:
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
            print_date = f"{print_date} {conns[0]} {second_date}"
        if len(days) > 2:
            print_date = dummy
        end_date = date(year=years[-1], month=months[-1],
                        day=days[-1]).strftime('%Y-%m-%d')
        return date_string, print_date, sorting_date, month_date, end_date
