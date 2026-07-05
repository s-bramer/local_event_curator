import os
import re
import time
import logging
import pandas as pd
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

# identifies this project per Nominatim's usage policy (https://operations.osmfoundation.org/policies/nominatim/)
headers = {
    'User-Agent': 'local-event-curator/1.0 (+https://github.com/s-bramer/local_event_curator)'
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

# Nominatim's usage policy caps requests at 1/sec
_NOMINATIM_MIN_INTERVAL = 1.0
_last_nominatim_request_time = 0.0

def _throttle_nominatim():
    global _last_nominatim_request_time
    elapsed = time.monotonic() - _last_nominatim_request_time
    if elapsed < _NOMINATIM_MIN_INTERVAL:
        time.sleep(_NOMINATIM_MIN_INTERVAL - elapsed)
    _last_nominatim_request_time = time.monotonic()

ADDRESS_DB_PATH = "addresses_db.csv"
FUZZY_MATCH_THRESHOLD = 93  # conservative - avoids merging two distinct venues
_address_db_cache = None  # lazy-loaded, held in memory for the life of the run

def _normalize_key(text: str) -> str:
    return re.sub(r'\s+', ' ', str(text).strip().lower())

def _load_address_db() -> pd.DataFrame:
    """load addresses_db.csv once per run instead of on every lookup"""
    global _address_db_cache
    if _address_db_cache is None:
        df = pd.read_csv(ADDRESS_DB_PATH, header=0, index_col=None)
        df['_normalized_name'] = df['name'].map(_normalize_key)
        _address_db_cache = df
    return _address_db_cache

def _find_cached_address(address_string: str):
    """exact (normalized) or fuzzy match against the in-memory address cache; returns a row or None"""
    df = _load_address_db()
    if df.empty:
        return None
    normalized = _normalize_key(address_string)
    exact = df[df['_normalized_name'] == normalized]
    if not exact.empty:
        return exact.iloc[0]
    match = process.extractOne(
        normalized, df['_normalized_name'], scorer=fuzz.WRatio, score_cutoff=FUZZY_MATCH_THRESHOLD)
    if match is not None:
        _, score, idx = match
        row = df.iloc[idx]
        logger.info(f"Fuzzy-matched address {address_string!r} to {row['name']!r} (score={score:.1f})")
        return row
    return None

def _add_cached_address(new_row: dict):
    """append a new lookup result to addresses_db.csv atomically and refresh the in-memory cache"""
    global _address_db_cache
    df = _load_address_db().drop(columns=['_normalized_name'])
    updated = pd.concat([df, pd.DataFrame([new_row])], axis=0, ignore_index=True)
    tmp_path = ADDRESS_DB_PATH + ".tmp"
    updated.to_csv(tmp_path, index=False)
    os.replace(tmp_path, ADDRESS_DB_PATH)
    updated['_normalized_name'] = updated['name'].map(_normalize_key)
    _address_db_cache = updated

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
        return postcodes[0]

    #2. try finding it via the OpenStreetMap Nominatim API (rate-limited per its usage policy)
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "countrycodes": "gb",
        "addressdetails": 1
    }
    _throttle_nominatim()
    try:
        response = SESSION.get(base_url, params=params, timeout=DEFAULT_TIMEOUT)
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        logger.warning(f"Nominatim lookup failed for {address!r}: {e}")
        return "ERROR: postcode not found"

    if response.status_code == 200 and data:
        first_result = data[0]
        if "address" in first_result and "postcode" in first_result["address"]:
            return first_result["address"]["postcode"]

    logger.info(f"Location unresolved via Nominatim for {address!r}")
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
    # 1. check if address already in the (in-memory, exact-or-fuzzy matched) database cache
    cached = _find_cached_address(address_string)
    if cached is not None:
        postcode = cached['postcode']
        town = cached['town']
        council = cached['council']
        full_address = cached['full_address']
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
        # add new entry to the address database (atomic write + refresh the in-memory cache)
        new_row = {'name': address_string, 'full_address': full_address,
                   'postcode': postcode, 'council': council, 'town': town}
        _add_cached_address(new_row)
        logger.info(f"New entry added to address DB: {list(new_row.values())}")
    try:
        council_abbr = COUNCIL_ABBR[council]
    except KeyError:
        council_abbr = 'out'
    
    short_address = full_address.split(',')[0]
    return postcode, town, council, council_abbr, full_address, short_address