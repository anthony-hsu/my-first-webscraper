from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import json
import locale


# Global
BR = ["all", "bed0", "bed1", "bed2"]
aptData = []
chrome_options = Options()
chrome_options.add_argument('--headless')
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
chrome_options.add_argument('user-agent={0}'.format(user_agent))
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 10)


# Functions

def isValid(data, maxPrice): 
  if locale.atof(data["price"].strip("$").replace(",", "")) > int(maxPrice):
    return False
  else:
    return True

def scrapeApartment(numBedsString, maxPrice):
  aptName = driver.find_element(By.ID, "propertyName").get_attribute("textContent").strip()
  try:
    element = wait.until(EC.presence_of_element_located((By.ID, "pricingView")))
    unitArray = element.find_element(By.XPATH, f".//div[@data-tab-content-id='{numBedsString}']").find_elements(By.CLASS_NAME, "hasUnitGrid")
    for unit in unitArray:
      modelInfo = unit.find_element(By.CLASS_NAME, "priceGridModelWrapper")
      modelName = modelInfo.find_element(By.XPATH, ".//span[@class='modelName']").get_attribute("textContent").strip()
      beds = modelInfo.find_element(By.XPATH, ".//span[@class='detailsTextWrapper']").get_attribute("textContent").strip().split(",")[0].strip()
      baths = modelInfo.find_element(By.XPATH, ".//span[@class='detailsTextWrapper']").get_attribute("textContent").strip().split(",")[1].strip()
      unitRows = unit.find_element(By.CLASS_NAME, "unitGridContainer").find_elements(By.XPATH, ".//li[contains(@class, 'unitContainer')]")
      for unitRow in unitRows:
        data = {}
        data["aptName"] = aptName
        data["modelName"] = modelName
        data["beds"] = beds
        data["baths"] = baths
        data["unit"] = unitRow.get_attribute("data-unit").strip()
        unitPrice = unitRow.find_element(By.XPATH, ".//div[contains(@class,'pricingColumn')]").find_element(By.XPATH, ".//span[@data-unitname]")
        data["price"] = unitPrice.get_attribute("textContent").strip()
        unitSqft = unitRow.find_element(By.XPATH, ".//div[@class = 'sqftColumn column']").find_element(By.XPATH, ".//span[not(@class)]")
        data["sqft"] = unitSqft.get_attribute("textContent").strip()
        unitAvail = unitRow.find_element(By.XPATH, ".//span[contains(@class,'dateAvailable')]")
        data["availability"] = unitAvail.get_attribute("textContent").strip().split("\n")[-1].strip()
        if isValid(data, maxPrice):
          aptData.append(data)
  except:
    print(f"ERROR: Skipping {aptName}")

def runScraper(neighborhood, city, state, numBeds, maxPrice):
  # # Parameters
  url = f"https://www.apartments.com/{neighborhood.replace(" ", "-")}-{city}-{state}/pet-friendly-dog/washer-dryer/"
  numBedsString = BR[int(numBeds)+1 if len(numBeds) > 0 else 0]
  driver.get(url)
  wait.until(EC.presence_of_element_located((By.CLASS_NAME, "placard")))
  cards = driver.find_elements(By.CLASS_NAME, "placard")
  original_window = driver.current_window_handle
  listingUrls = []
  for card in cards:
    listingUrls.append(card.get_attribute("data-url"))
  for listingUrl in listingUrls:
    try:
      driver.switch_to.new_window('tab')
      driver.get(listingUrl)
      wait.until(EC.presence_of_element_located((By.ID, "propertyName")))
      scrapeApartment(numBedsString, maxPrice)
      driver.close()
      driver.switch_to.window(original_window)
    except:
      print(f"Apartment page not found... skipping!")
    finally:
      continue  
  jsonData = json.dumps(aptData)
  df = pd.read_json(jsonData)
  df.to_csv(f"{neighborhood}_{"all" if len(numBeds) == 0 else f"{numBeds}BR"}_{maxPrice}.csv", index=False)
  driver.quit()


# Run

runScraper("Capitol Hill", "Seattle", "WA", "1", 2800)