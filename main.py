from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import json
import locale
import time

url = "https://www.apartments.com/"
neighborhood = "Capitol Hill"
city = "Seattle"
state = "WA"
searchKeyword = f"{neighborhood}, {city}, {state}"
BR = ["all", "bed0", "bed1", "bed2"]
numBeds = BR[2]
maxPrice = 2200
aptData = []

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 10)

def isValid(data):
  if locale.atof(data["price"].strip("$").replace(",", "")) > maxPrice:
    return False
  else:
    return True
  
def selectFilters(filters):
  try:
    filtersDropdown = wait.until(EC.presence_of_element_located((By.ID, "advancedFiltersIcon")))
    wait.until(EC.element_to_be_clickable(filtersDropdown))
    filtersDropdown.click()
    filtersContainer = wait.until(EC.presence_of_element_located((By.ID, "advancedFiltersContainer")))
    for filter in filters:
      if filter == "dog":
        filterName = "PetFriendly_1"
      elif filter == "laundry":
        filterName = "UnitAmenities_2"
      checkbox = filtersContainer.find_element(By.ID, filterName)
      checkbox.click()
      time.sleep(2)
    doneButton = filtersContainer.find_element(By.CLASS_NAME, "done")
    wait.until(EC.element_to_be_clickable(doneButton))
    doneButton.click()
  except:
    print(f"Error found while selecting filters!")

def scrapeApartment():
  aptName = driver.find_element(By.ID, "propertyName").get_attribute("textContent").strip()
  try:
    element = wait.until(EC.presence_of_element_located((By.ID, "pricingView")))
    unitArray = element.find_element(By.XPATH, f".//div[@data-tab-content-id='{numBeds}']").find_elements(By.CLASS_NAME, "hasUnitGrid")
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
        unitTitle = unitRow.find_element(By.XPATH, ".//div[contains(@class, 'unitColumn')]").find_element(By.XPATH, "//span[@title]").get_attribute("textContent").strip()
        data["unit"] = unitTitle
        unitPrice = unitRow.find_element(By.XPATH, ".//div[contains(@class,'pricingColumn')]").find_element(By.XPATH, ".//span[@data-unitname]")
        data["price"] = unitPrice.get_attribute("textContent").strip()
        unitSqft = unitRow.find_element(By.XPATH, ".//div[@class = 'sqftColumn column']").find_element(By.XPATH, ".//span[not(@class)]")
        data["sqft"] = unitSqft.get_attribute("textContent").strip()
        unitAvail = unitRow.find_element(By.XPATH, ".//span[contains(@class,'dateAvailable')]")
        data["availability"] = unitAvail.get_attribute("textContent").strip().split("\n")[-1].strip()
        if isValid(data):
          aptData.append(data)
  except:
    print(f"ERROR: Skipping {aptName}")



driver.get(url)

searchInput = wait.until(EC.presence_of_element_located((By.ID, "quickSearchLookup")))
searchInput.click()
searchInput.send_keys(searchKeyword)
time.sleep(2)
searchInput.send_keys(Keys.ENTER)
searchButton = driver.find_element(By.CLASS_NAME, "go")
searchButton.click()
selectFilters(["dog", "laundry"])
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "placard")))
cards = driver.find_elements(By.CLASS_NAME, "placard")
listingIds = []
for card in cards: listingIds.append(card.get_attribute("data-listingid"))
for listingId in listingIds:
  wait.until(EC.presence_of_element_located((By.XPATH, ".//article[@data-listingid='"+listingId+"']")))
  card = driver.find_element(By.XPATH, ".//article[@data-listingid='"+listingId+"']")
  cardLink = card.find_element(By.CLASS_NAME, "property-link")
  try: 
    wait.until(EC.element_to_be_clickable(cardLink))
    cardLink.click()
    try:
      wait.until(EC.presence_of_element_located((By.ID, "propertyName")))
      scrapeApartment()
      driver.execute_script("window.history.go(-1)")
    except:
      print(f"Apartment page not found... skipping {listingId}")
    finally:
      continue
  except:
    print(f"Card not clickable... skipping {listingId}")
  finally:
    continue

jsonData = json.dumps(aptData)
df = pd.read_json(jsonData)
df.to_csv("output.csv", index=False)

driver.quit()