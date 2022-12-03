#THIS FILE IS JUST FOR TESTING CODE#
#DELETE ME!!#
import re
import pandas as pd
import time
import calendar
from datetime import date, datetime
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

# chrome_options = Options()
# chrome_options.add_argument("--headless")
# driver = webdriver.Chrome("C://Users//Stefan.Bramer//HOME//PROJECTS//CODING//tools//chromedriver.exe", options=chrome_options)
# url ="https://www.wmc.org.uk/en/whats-on/events/"
# try:
# 	driver.get(url)
# except Exception as e:
# 	driver.quit()
# else:
#     #element = driver.find_elements(By.TAG_NAME, 'a')
#     all_href = driver.find_elements(By.XPATH,  "//*[contains(@href, '/whats-on/')]")
# for ref in all_href:
# 	print(ref.text)
	
# # driver.save_screenshot('WebsiteScreenShot.png')
	
# driver.quit()


# def title_formatter(s:str):
# 	s = re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda word: word.group(0).capitalize(),s)
# 	for key,value in REPLACE_ME.items():
# 		s = s.replace(key,value)
# 	return s

# s = "The Bbc had a Swam of a night with Uwc WEIGHING in like a member of the Lgbtq community"


# print(title_formatter(s))

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36'}
address = "Barry Town Centre, Holton Road, Park Crescent, High Street & Goodsheds"
address = "Goodsheds, Hood Road, Barry, Vale of Glamorgan"
address = "St Fagans National Museum of History"

r=requests.get(f'https://www.google.com/search?q={address}+Wales+UK+Postcode',headers=headers, timeout =10)
soup = BeautifulSoup(r.content,"html5lib")
postcode = re.findall("[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][ABD-HJLNP-UW-Z]{2}", soup.text)[0]
# address = soup.find('span',class_="LrzXr").text
# print(len(postcodes))
print(postcode)