import time
import sys
sys.path.append('../../')
#import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from flask_api.order_status_db import update_order_processing, update_order_completed, update_order_failed

#Custom esceptions

class openErpException(Exception):
    pass

class loginException(Exception):
    pass

class handlingException(Exception):
    pass



# Set up the WebDriver and ActionChains for chrome

options = Options()
options.add_argument("--headless=new")


def create_orderline(dealer, worksheet, product_nr, product_amount, unique_id, user, password,logging,order_status_db):
    # Check if it nessesary to create a new driver for each call
    driver = webdriver.Chrome(options=options)
    actions = ActionChains(driver)
    try:
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logging.info(f"\n\n*****************************************************************************************")
        logging.info(f"Creating orderline: {dealer}, {worksheet}, {product_nr}, {product_amount} at {create_time}")
        update_order_processing(unique_id,order_status_db)
        #raise handlingException(f"Creating orderline for dealer: {dealer} at {create_time} failed with exception: {e}")
        try:
            # Navigate to the login page
            driver.get("https://manager.addanmark.dk/login")
            driver.set_window_size(1683, 517)
        except Exception as e:
            logging.error(f": Login failed with exception: {e}")
            raise openErpException("Falied to open admanager: {e}")

        # Perform login actions
        try:
            driver.find_element(By.CSS_SELECTOR, "mat-form-field.ng-tns-c40-3 div.mat-form-field-flex > div").click()
            driver.find_element(By.ID, "mat-input-0").send_keys(user)
            driver.find_element(By.CSS_SELECTOR, "mat-form-field.ng-tns-c40-4 div.mat-form-field-flex > div").click()
            driver.find_element(By.ID, "mat-input-1").send_keys(password)
            driver.find_element(By.TAG_NAME, "button").click()
        except Exception as e:
            logging.error(f": Login failed with exception: {e}")
            raise loginException("Login failed: {e}")

        # Open worksheet(Arbejdskort) overview
        try:
            time.sleep(.5)  # Wait for the page to load
            driver.find_element(By.CSS_SELECTOR, "a:nth-of-type(5) > mat-icon").click()
            time.sleep(.5)  # Wait for the products page to load

                # Traverse the table of worksheets to ensure the input worksheet exists
            worksheet_found = False

            table = driver.find_element(By.TAG_NAME, "table")
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells[0].text == worksheet:
                    logging.info(f"Worksheet {worksheet} found")
                    worksheet_found = True
                    break
        except:
            logging.error(f"RPA steps to locate worksheet failed {worksheet} for dealer {dealer}: {e}")
            raise handlingException(f"RPA steps to locate worksheet failed {worksheet} for dealer {dealer}: {e}")

        if not worksheet_found:
            logging.error(f": Worksheet {worksheet} for dealer {dealer} not found at {create_time}")
            raise handlingException(f"Worksheet {worksheet} for dealer {dealer}")
        else:
            # Open the located worksheet
            time.sleep(.5)
            try:
                cells[0].click()
            except Exception as e:
                logging.info(f": Failed to open Worksheet {worksheet}")
                raise handlingException(f": Failed to open Worksheet {worksheet} for dealer {dealer}: {e}")
            
            time.sleep(.5)  # Wait for the page to load
        
            try:
                logging.info(f"Checking for existing orderlines for product: {product_nr} worksheet: {worksheet}")
                line_list = driver.find_element(By.TAG_NAME, "worksheet-line-list")
                

                # Orderline already exists, calculate the amount to be added as the difference between the ordered amount and the sum of existing orderlines
                logging.info(f"Orderline for product {product_nr} already exists")
                exist_lines = line_list.find_elements(By.TAG_NAME, "worksheet-line-row")
                if len(exist_lines) > 0:
                    existing_lines_list = []
                    oilmat_line_amount_sum = 0
                    other_line_amount_sum = 0
                    for line in exist_lines:
                        print(line)
                        varenummer = line.find_element(By.CSS_SELECTOR, "[class='product-number']").text
                        if varenummer == product_nr:
                            varenavn = line.find_element(By.CSS_SELECTOR, "[class='product-name']").text
                            antal = line.find_element(By.CSS_SELECTOR, "[class='product-amount-amount']").text
                            existing_lines_list.append([varenummer,varenavn,antal])
                            if "OilMat" in varenavn:
                                oilmat_line_amount_sum += int(antal)
                            else:
                                other_line_amount_sum += int(antal)

                    logging.debug(f"Existing varenummer,varenavn,antal: {varenummer} , {varenavn}, {antal}")

                calc_amount = int(product_amount)
            except Exception as e:
                logging.info(f"Failed to handle existing orderlines for worksheet {worksheet}: {e}")
                raise handlingException(f"Failed to handle existing orderlines for worksheet {worksheet}: {e}")

            # Create orderline, this part created a lot of problems submitting and the combination of keys to do the trick was found by trial and error
            # This section is wery fragile and may break if the site is updated or with minor changes that seems small 
            try:
                varenummer_input = driver.find_element(By.CSS_SELECTOR, "[data-placeholder='Varenummer']")
                varenummer_input.clear()
                varenummer_input.send_keys(str(product_nr))
                varenummer_input.send_keys(Keys.TAB)
                time.sleep(.5) 
                #qdriver.refresh()
                varenavn_input = driver.find_element(By.CSS_SELECTOR, "[data-placeholder='Varenavn']")
                #driver.execute_script("arguments[0].innerText += ' -- OilMat: 000001';", varenavn_input)
                varenavn_input.click()

                print(varenavn_input.text)         
                varenavn_input.send_keys(' -- OilMat:' + unique_id)
                varenavn_input.send_keys(Keys.TAB)

                time.sleep(.5) 
                antal_input = driver.find_element(By.CSS_SELECTOR, "[data-placeholder='Antal']")
                antal_input.click() 
                antal_input.clear()
                antal_input.send_keys(str(calc_amount))
                # Acorrding to documentation varenummer_input.send_keys(Keys.ENTER) should have posted the orderline, but it did not work
                # The next 5 lines compensates
                #varenummer_input.send_keys(Keys.TAB)
                time.sleep(.5) 
                #Key press must be performed without any element selected
                actions.send_keys(Keys.ENTER)
                actions.perform()

                # Orderline created 
                logging.info(f"Orderline created: {dealer}, {worksheet}, {product_nr}, {product_amount} at {create_time}")
                logging.info(f"\n*****************************************************************************************")
                update_order_completed(unique_id,order_status_db)

            except Exception as e:
                logging.info(f"Creating orderline for dealer: {dealer} at {create_time} failed")
                raise handlingException(f"Creating orderline for dealer: {dealer} at {create_time} failed: {e}")

    except Exception as e:
        update_order_failed(unique_id,order_status_db)
        raise
        # Send mail 
    finally:
        # Close the WebDriver
        time.sleep(1) 
        driver.quit()

def main(argv):
   dealer =  argv[0] 
   worksheet =  argv[1] 
   product_nr =  argv[2] 
   product_amount =  argv[3]
   unique_id=  argv[4]
   user =  argv[5] 
   password =  argv[6] 

   create_orderline(dealer, worksheet, product_nr, product_amount,unique_id,user,password)

if __name__ == "__main__":
   main(sys.argv[1:])