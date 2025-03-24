import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

class loginException(Exception):
    pass

class worksheetNotFoundException(Exception):
    pass

class openWorksheetException(Exception):
    pass

def create_orderline(dealer, worksheet_id, product_nr, product_amount, user, password):
    try:
        options = Options()
        #options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        actions = ActionChains(driver)
        
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logging.info(f"\n\n*****************************************************************************************")
        logging.info(f"Creating orderline: {dealer}, {worksheet_id}, {product_nr}, {product_amount} at {create_time}")

        try:
            # Navigate to the login page
            driver.get("https://auth.cac.dk/Account/Login")
            driver.set_window_size(1728, 1055)

            try:
                driver.find_element(By.ID, "inputEmail").send_keys("TAthomas")
                driver.find_element(By.ID, "inputPassword").click()
                driver.find_element(By.ID, "inputPassword").send_keys("TAthomas77")
                driver.find_element(By.CSS_SELECTOR, ".btn").click()
            except Exception as e:
                logging.error(f": Login failed with exception: {e}")
                raise loginException("Login failed")
            
            # Open worksheet(Arbejdskort) overview
                #time.sleep(2)  # Wait for the page to load
                #try:
            driver.find_element(By.LINK_TEXT, "Åben kundestyring").click()
            driver.find_elements(By.TAG_NAME, "sb-worksheet-list")
            # Check if the worksheet exists and is active
            worksheet = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='font-bold' and text()='#36993 ']"))
            )
            worksheet.click()
            time.sleep(3)

            # Wait for the worksheet page to load
            #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "worksheetPageLoaded")))

            # Locate the product number input field
            product_number_input = driver.find_elements(By.CSS_SELECTOR, "[col-id='productnumber']")

            # Type the product number
            product_number_input[1].send_keys(product_nr)

            # Simulate pressing Enter to trigger autocomplete
            product_number_input[1].send_keys(Keys.ENTER)

            # Wait for the autocomplete to complete
            wait = WebDriverWait(driver, 10)
            product_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[col-id='productname']"))).text

            print(f"Product Name: {product_name}")

        except Exception as e:
            logging.error(f"Failed to create order line: {e}")
            raise

        finally:
            driver.quit()

    except Exception as e:
        logging.error(f"Failed to create order line: {e}")
        raise

def main(argv):
    dealer = argv[0]
    worksheet_id = argv[1]
    product_nr = argv[2]
    product_amount = argv[3]
    user = argv[4]
    password = argv[5]

    create_orderline(dealer, worksheet_id, product_nr, product_amount, user, password)

if __name__ == "__main__":
    main(sys.argv[1:])