import requests

url = "https://www.wmc.org.uk/en/whats-on/json/5"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)
data = response.json()

# Explore the structure
unique_event_urls = set()

for item in data:
    event_url = item.get("event_url")
    if event_url:
        unique_event_urls.add(event_url)

print(list(unique_event_urls))