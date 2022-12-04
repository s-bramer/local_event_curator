import pandas as pd
import re
from bs4 import BeautifulSoup
import requests


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
}

COUNCIL_ABBR = {
    'Cardiff': 'cff',
    'Gwynedd': 'out',
    'Swansea': 'swa',
    'Vale of Glamorgan': 'vog',
    'Carmarthenshire': 'out',
    'Rhondda Cynon Taf': 'rct',
    'Neath Port Talbot': 'oth',
    'Monmouthshire': 'oth',
    'Newport': 'oth',
    'Torfaen': 'oth',
    'Powys': 'out',
    'Caerphilly': 'oth',
    'Bridgend': 'brd',
    'Digital Event': 'oth',
}


def get_postcode(address: str):
    """find postcode in address string or (if not) online with google"""
    # 1. see if it is contained in the address string
    postcodes = re.findall(
        "[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", address)
    if len(postcodes) > 0:
        # return f"{postcodes[0]} from address string (1)"
        return postcodes[0]
    else:
        # 2. try to find postcode online
        try:
            r = requests.get(
                f'https://www.google.com/search?q={address}+Wales+UK+Postcode', headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, "html5lib")
            postcode = re.findall(
                "[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", soup.text)[0]
        except:
            return "ERROR: postcode not found"
        else:
            return postcode


def get_council(postcode: str):
    """find council online at checkmypostcode.co.uk"""
    council = ""
    try:
        r = requests.get(
            f"https://checkmypostcode.uk/{postcode.replace(' ','')}", headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, "html5lib")
        results = soup.find_all("div", attrs={"class": "medium-5 columns"})
        for x, item in enumerate(results):
            if item.text.strip() == "Local Authority":
                council = results[x+1].text
                break
    except:
        return "ERROR: council not found"
    else:
        return council.strip()


def get_town(postcode: str):
    """find town online at checkmypostcode.co.uk"""
    town = ""
    try:
        r = requests.get(
            f"https://checkmypostcode.uk/{postcode.replace(' ','')}", headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, "html5lib")
        results = soup.find_all("div", attrs={"class": "medium-5 columns"})
        for x, item in enumerate(results):
            if item.text.strip() == "Built-up Area":
                town = results[x+1].text
                break
    except:
        return "ERROR: town not found"
    else:
        return town.strip().replace(' ', '')


def sniff_sniff(address_string: str):
    """returns postcode, town, council and council_abbr from address string"""
    # 1. check if address already in database
    df_adressess_db = pd.read_csv("addresses_db.csv", header=0, index_col=None)
    if address_string in df_adressess_db['name'].values:
        postcode = (
            df_adressess_db.loc[df_adressess_db['name'] == address_string, 'postcode'].iloc[0])
        town = (df_adressess_db.loc[df_adressess_db['name']
                == address_string, 'town'].iloc[0]).replace(' ', '')
        council = (
            df_adressess_db.loc[df_adressess_db['name'] == address_string, 'council'].iloc[0])
        full_address = (
            df_adressess_db.loc[df_adressess_db['name'] == address_string, 'full_address'].iloc[0])
    else:
        postcode = get_postcode(address_string)
        if "ERROR" in postcode:
            return 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX'
        else:
            council = get_council(postcode)
            if "ERROR" in council:
                return postcode, 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX'
            else:
                town = get_town(postcode)
                if "ERROR" in town:
                    return postcode, council, 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX'
                else:
                    if town.lower() == "castle":
                        town = council
        if len(re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", address_string)) > 0:
            full_address = address_string
        else:
            full_address = address_string + ", " + postcode
        # add new entry to the address database
        new_row = {'name': address_string, 'full_address': full_address,
                   'postcode': postcode, 'council': council, 'town': town}
        df_adressess_db = df_adressess_db.append(new_row, ignore_index=True)
        df_adressess_db.to_csv("addresses_db.csv", index=False)
        print("NEW ENTRY IN ADDRESS DATABASE!")
    try:
        council_abbr = COUNCIL_ABBR[council]
    except:
        council_abbr = 'out'
    short_address = full_address.split(',')[0]
    return postcode, town, council, council_abbr, full_address, short_address
