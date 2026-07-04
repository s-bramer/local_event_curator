import pandas as pd
import re
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
}

# reasonable timeout + shared session with retry/backoff for transient network errors
DEFAULT_TIMEOUT = 30

def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(headers)
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

SESSION = _build_session()

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

def get_postcode(address):
    #1. see if postcode is contained in the address string
    postcodes = re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", address)
    if len(postcodes) > 0:
        # return f"{postcodes[0]} from address string (1)"
        return postcodes[0]
    else:
        #2. try finding it via open streetmap API
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": address,
            "format": "json",
            "countrycodes": "gb",
            "addressdetails": 1
        }
        try:
            response = SESSION.get(base_url, params=params, timeout=DEFAULT_TIMEOUT)
            data = response.json()
            nominatim_ok = response.status_code == 200 and data
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"Nominatim lookup failed for {address!r}: {e}")
            data = None
            nominatim_ok = False

        if nominatim_ok:
            if len(data) > 0:
                first_result = data[0]
                if "address" in first_result and "postcode" in first_result["address"]:
                    return first_result["address"]["postcode"]
                else:
                    return "ERROR: postcode not found"
            else:
                return "ERROR: postcode not found"
        else:
            #3. try to duckduckgo to find postcode (first postcode in search scrape text)
            base_url = "https://duckduckgo.com/html/"
            params = {"q": f"{address} Wales UK Postcode"}
            try:
                r = SESSION.get(base_url, params=params, timeout=DEFAULT_TIMEOUT)
                soup = BeautifulSoup(r.content, "html5lib")
            except requests.RequestException as e:
                logger.warning(f"DuckDuckGo postcode fallback failed for {address!r}: {e}")
                return "ERROR: postcode not found"

            if r.status_code == 200:
                matches = re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", soup.text)
                if matches:
                    return matches[0]
                else:
                    return "ERROR: postcode not found"
            else:
                return "ERROR: postcode not found"

def get_council(postcode: str):
    """find council online at checkmypostcode.co.uk"""
    council = ""
    try:
        r = SESSION.get(
            f"https://checkmypostcode.uk/{postcode.replace(' ','')}", timeout=DEFAULT_TIMEOUT)
        soup = BeautifulSoup(r.content, "html5lib")
        results = soup.find_all("div", attrs={"class": "medium-5 columns"})
        for x, item in enumerate(results):
            if item.text.strip() == "Local Authority":
                council = results[x+1].text
                break
    except requests.RequestException as e:
        logger.warning(f"Council lookup network error for postcode {postcode!r}: {e}")
        return "ERROR: council not found"
    except (AttributeError, IndexError):
        logger.warning(f"Council lookup page structure unexpected for postcode {postcode!r} (site markup may have changed)")
        return "ERROR: council not found"
    else:
        return council.strip()


def get_town(postcode: str):
    """find town online at checkmypostcode.co.uk"""
    town = ""
    try:
        r = SESSION.get(
            f"https://checkmypostcode.uk/{postcode.replace(' ','')}", timeout=DEFAULT_TIMEOUT)
        soup = BeautifulSoup(r.content, "html5lib")
        results = soup.find_all("div", attrs={"class": "medium-5 columns"})
        for x, item in enumerate(results):
            if item.text.strip() == "Built-up Area":
                town = results[x+1].text
                break
    except requests.RequestException as e:
        logger.warning(f"Town lookup network error for postcode {postcode!r}: {e}")
        return "ERROR: town not found"
    except (AttributeError, IndexError):
        logger.warning(f"Town lookup page structure unexpected for postcode {postcode!r} (site markup may have changed)")
        return "ERROR: town not found"
    else:
        return town.strip()

def sniff_sniff(address_string: str):
    """returns postcode, town, council and council_abbr from address string"""
    # 1. check if address already in database
    df_adressess_db = pd.read_csv("addresses_db.csv", header=0, index_col=None)
    if address_string in df_adressess_db['name'].values:
        postcode = (df_adressess_db.loc[df_adressess_db['name'] == address_string, 'postcode'].iloc[0])
        town = (df_adressess_db.loc[df_adressess_db['name']== address_string, 'town'].iloc[0])
        council = (df_adressess_db.loc[df_adressess_db['name'] == address_string, 'council'].iloc[0])
        full_address = (df_adressess_db.loc[df_adressess_db['name'] == address_string, 'full_address'].iloc[0])
    else:
        try:
            postcode = get_postcode(address_string)
        except (requests.RequestException, ValueError, IndexError) as e:
            logger.error(f"ERROR: Postcode not found: >{address_string}<! ({e})")
            return 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX'
        if "ERROR" in postcode:
            logger.error(f"ERROR: Postcode not found: {address_string}!")
            return 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX'
        else:
            council = get_council(postcode)
            if "ERROR" in council:
                logger.error(f"ERROR: Council not found with postcode: {postcode}!")
                return postcode, 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX'
            else:
                town = get_town(postcode)
                if "ERROR" in town:
                    logger.error(f"ERROR: Town not found with postcode: {postcode}!")
                    return postcode, council, 'XXXXXX', 'XXXXXX', 'XXXXXX', 'XXXXXX'
                else:
                    if town.lower() == "castle":
                        town = council
        if len(re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", address_string)) > 0:
            full_address = address_string
        else:
            full_address = address_string + ", " + postcode
        # add new entry to the address database
        new_row = pd.DataFrame([{'name': address_string, 'full_address': full_address,
                   'postcode': postcode, 'council': council, 'town': town}])
        #df_adressess_db = df_adressess_db.append(new_row, ignore_index=True) # append method is deprecated
        df_adressess_db = pd.concat([df_adressess_db, new_row], axis=0, ignore_index=True)
        #df_adressess_db = pd.concat([df_adressess_db, new_row], ignore_index=True)
        df_adressess_db.to_csv("addresses_db.csv", index=False)
        logger.error(f" INFO: New Entry Added to address DB. {new_row.iloc[0].values.tolist()}")
    try:
        council_abbr = COUNCIL_ABBR[council]
    except KeyError:
        council_abbr = 'out'
    
    short_address = full_address.split(',')[0]
    return postcode, town, council, council_abbr, full_address, short_address