import pandas as pd
import re
from bs4 import BeautifulSoup
import requests
headers={
'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
}

COUNCIL_ABBR = {
    'Cardiff' : 'cff',
    'Gwynedd' : 'out',
    'Swansea' : 'swa',
    'Vale of Glamorgan' : 'vog', 
    'Carmarthenshire' : 'out',
    'Rhondda Cynon Taf': 'rct', 
    'Neath Port Talbot' : 'oth',
    'Monmouthshire' : 'oth',
    'Newport' : 'oth',
    'Torfaen' : 'oth',
    'Powys' : 'out',
    'Caerphilly' : 'oth',
    'Bridgend' : 'brd',
    'digital' : 'oth',
}

def get_postcode(address:str):
    #1. see if it is contained in the address string
    postcodes = re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", address)
    if len(postcodes) > 0:
        # return f"{postcodes[0]} from address string (1)"
        return postcodes[0]
    else:
    #2. try to find postcode online
        try: 
            r=requests.get(f'https://www.google.com/search?q={address}+Wales+UK+Postcode',headers=headers, timeout =10)
            soup = BeautifulSoup(r.content,"html5lib")
            postcode = re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", soup.text)[0]
        except:
            return "ERROR: postcode not found"
        else:
            return postcode
        
def get_council(postcode:str):
    #get coucil online
    council = ""
    try:
        r=requests.get(f"https://checkmypostcode.uk/{postcode.replace(' ','')}",headers=headers, timeout =10)
        soup = BeautifulSoup(r.content,"html5lib")
        results = soup.find_all("div", attrs={"class":"medium-5 columns"})
        for x,item in enumerate(results):
            if item.text.strip() == "Local Authority":
                council = results[x+1].text
                break
    except:
        return "ERROR: council not found"
    else:
        return council.strip()

def get_town(postcode:str):
    # find town online
    town = ""
    try:
        r=requests.get(f"https://checkmypostcode.uk/{postcode.replace(' ','')}",headers=headers, timeout =10)
        soup = BeautifulSoup(r.content,"html5lib")
        results = soup.find_all("div", attrs={"class":"medium-5 columns"})
        for x,item in enumerate(results):
            if item.text.strip() == "Built-up Area":
                town = results[x+1].text
                break
    except:
        return "ERROR: town not found"
    else:
        return town.strip().replace(' ','')

def sniff_sniff(address_string:str):
    """returns postcode, town, council and council_abbr from address string"""
    #1. check if address already in database 
    df_adressess_db = pd.read_csv("addresses_db.csv", header=0, index_col=None)
    if address_string in df_adressess_db['name'].values:
        postcode = (df_adressess_db.loc[df_adressess_db['name'] == address_string, 'postcode'].iloc[0])
        town = (df_adressess_db.loc[df_adressess_db['name'] == address_string, 'town'].iloc[0]).replace(' ','')
        council = (df_adressess_db.loc[df_adressess_db['name'] == address_string, 'council'].iloc[0])
        full_address = (df_adressess_db.loc[df_adressess_db['name'] == address_string, 'full_address'].iloc[0])
    else:
        postcode = get_postcode(address_string)
        if "ERROR" in postcode:
            return 'XXXXXX', 'XXXXXX','XXXXXX','XXXXXX','XXXXXX','XXXXXX'
        else:
            council = get_council(postcode)
            if "ERROR" in council:
                return postcode, 'XXXXXX','XXXXXX','XXXXXX','XXXXXX','XXXXXX'
            else:
                town = get_town(postcode)
                if "ERROR" in town:
                    return postcode, council, 'XXXXXX','XXXXXX','XXXXXX','XXXXXX'
                else:
                    if town.lower() == "castle":
                        town = council
        if len(re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", address_string)) > 0:
            full_address = address_string
        else:
            full_address = address_string + ", " + postcode
        #add new entry to the address database
        new_row = {'name' : address_string, 'full_address': full_address, 'postcode': postcode, 'council': council, 'town': town}
        df_adressess_db = df_adressess_db.append(new_row, ignore_index=True)
        df_adressess_db.to_csv("addresses_db.csv",index=False)
    try:
        council_abbr = COUNCIL_ABBR[council]
    except:
        council_abbr = 'out'
    short_address = full_address.split(',')[0]
    return postcode, town, council, council_abbr, full_address, short_address

    # address_string.replace(',','').replace(' ','+')
    # try:
    #     r=requests.get(f'https://www.google.com/search?q={address_string}+Wales+UK+Postcode',headers=headers, timeout =10)
    #     #r=requests.get(f'https://www.streetcheck.co.uk/search?s={address_string}+Wales+UK+Postcode',headers=headers, timeout =10)

    #     soup = BeautifulSoup(r.content,"html5lib")
    #     address = soup.find('span',class_="LrzXr").text
        
    #     #soup = soup.find("ul", attrs={"id": "searchresults"})
    #     #address = soup.find_all("a")[0].string

    # except:
    #     print("address not found")

    # else:
    #     #check if address contains postcode i.e. is an address
    #     if len(re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", address))>0:
    #         return address

# UPDATE ADDRESS_DB WITH POSTCODE AND COUNCIL        
# df_in = pd.read_csv("addresses_db.csv", header=0, index_col=None)
# df_out_path = "addresses_db.csv"
# for i, row in enumerate(range(0, len(df_in))):
#     #get postcode from address string
#     # if pd.isna(df_in.loc[row, ('postcode')]):
#     #     if not pd.isna(df_in.loc[row, ('address')]):
#     #         postcode = get_postcode(df_in.loc[row, ('address')])
#     #         if postcode is not None:
#     #             df_in.loc[row, ('postcode')] = postcode
#     # use postcode to get council area
#     # if not pd.isna(df_in.loc[row, ('postcode')]):
#     #     council = get_council(df_in.loc[row, ('postcode')])
#     #     if council is not None:
#     #         df_in.loc[row, ('council')] = council
#     if not pd.isna(df_in.loc[row, ('postcode')]):
#         town = get_town(df_in.loc[row, ('postcode')])
#         if town is not None:
#             df_in.loc[row, ('town')] = town
#     #use address string (often incomplete) to get full address 
#     # if pd.isna(df_in.loc[row, ('address')]):
#     #     address = get_address(df_in.loc[row, ('name')])
#     #     if address is not None:
#     #         df_in.loc[row, ('address')] = address    
# df_in.to_csv(df_out_path,index=False)

#IMPORT COUNCIL INFO INTO EVENT DATABASE
# df_in = pd.read_csv("events_database.csv", header=0, index_col=None)
# df_address_db = pd.read_csv("addresses_db.csv", header=0, index_col=None)
# df_in["council"] = ""
# df_in["council_abbr"] = ""
# df_out_path = "events_database_updated.csv"
# for i, row in enumerate(range(0, len(df_in))):
#     if 'digital' in df_in.loc[row, ('location')].lower():
#         council_name = 'digital'
#     else:
#         council_name = (df_address_db.loc[df_address_db['name'] == df_in.loc[row, ('location')], 'council'].iloc[0])
#     try:
#         council_name_abbr = COUNCIL_ABBR[council_name]
#     except:
#         council_name_abbr = 'out'
#     df_in.loc[row, ('council')] = council_name
#     df_in.loc[row, ('council_abbr')] = council_name_abbr
# df_in.to_csv(df_out_path,index=False)
        
# print(get_address("Fonmon Castle, Barry, Vale of Glamorgan"))
