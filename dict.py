#THIS FILE IS JUST FOR TESTING CODE#
#DELETE ME!!#
import re
import pandas as pd
import time
import calendar
from datetime import date, datetime
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By



chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome("C://Users//Stefan.Bramer//HOME//PROJECTS//CODING//tools//chromedriver.exe", options=chrome_options)
url ="https://www.wmc.org.uk/en/whats-on/events/"
try:
	driver.get(url)
except Exception as e:
	driver.quit()
else:
    #element = driver.find_elements(By.TAG_NAME, 'a')
    all_href = driver.find_elements(By.XPATH,  "//*[contains(@href, '/whats-on/')]")
for ref in all_href:
	print(ref.text)
	
# driver.save_screenshot('WebsiteScreenShot.png')
	
driver.quit()