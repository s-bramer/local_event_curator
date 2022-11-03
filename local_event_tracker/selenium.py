from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

chrome_options = Options()
chrome_options.add_argument("--headless") #keep browser hidden
chrome_driver_path = "C://Users//Stefan.Bramer//HOME//PROJECTS//CODING//tools//chromedriver.exe"
driver = webdriver.Chrome(executable_path=chrome_driver_path,chrome_options=chrome_options)
driver.get("https://www.visitthevale.com/events")

# entries = []
featured_item = driver.find_element(By.CLASS_NAME,"grid-item-100.w-dyn-item")

href = driver.find_element(By.CLASS_NAME,"primary-button.green.w-button").get_attribute('href')
print(featured_item.text)
print(href)

##for x, item in enumerate(driver.find_elements(By.CLASS_NAME,"grid-item-50.w-dyn-item")):
    #start = item.text.splitlines( )[0]
    #end = item.text.splitlines( )[2]
    #title = item.text.splitlines( )[3]
    #href = WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH,"//a[@class='full-image-link-card-50 w-inline-block']")))[x].get_attribute('href')
    ##image_link = driver.find_element(By.XPATH,"//a[@class='item-image full-image-link']")
    #entries.append({'title': title, 'start_date': start, 'end_date': end, 'link': href})
    #print(image_link)

# print(entries)

driver.quit()

