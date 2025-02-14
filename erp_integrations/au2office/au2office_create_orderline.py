import time
import sys
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#Custom esceptions

class loginException(Exception):
    pass

class worksheetNotFoundException(Exception):
    pass

class openWorksheetException(Exception):
    pass


# Set up the WebDriver and ActionChains for chrome

options = Options()
#options.add_argument("--headless=new")



logging.basicConfig(level=logging.INFO,filename='au2office_create_orderline.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def refresh_product_lines(driver):
    # Open the worksheet columns
    product_nrs  = driver.find_elements(By.CSS_SELECTOR, "[col-id='productnumber']")
    product_names  = driver.find_elements(By.CSS_SELECTOR, "[col-id='productname']")
    product_units  = driver.find_elements(By.CSS_SELECTOR, "[col-id='productUnit']")
    product_groups  = driver.find_elements(By.CSS_SELECTOR, "[col-id='productGroup']")
    product_amounts  = driver.find_elements(By.CSS_SELECTOR, "[col-id='numberOfItems']")
    product_prices  = driver.find_elements(By.CSS_SELECTOR, "[col-id='salesprice']")
    line_count = 0 

    col_elements_list = [product_nrs, product_names, product_units, product_groups, product_amounts, product_prices]
    done = False
    products_list = []
    print(f"product_nrs:{product_nrs}")

    # Create an array (list of lists) of productslines
    while not done:
        #logging.info(f"product:{product_names[line_count].accessible_name}:")
        logging.info(f"product_nr:{product_nrs[line_count].accessible_name}:")

        if product_nrs[line_count].accessible_name == "Varenummer":
            line_count += 1
            # This is the header line, skip it

        logging.info(f"Handling line{line_count}:")
        product_line_list = []
        for col in col_elements_list:
            logging.info(f"Handling col for line{line_count}:")
            field_dict = {}
            field_dict['element'] = col[line_count]
            field_dict['value'] = col[line_count].accessible_name
            product_line_list.append(field_dict)
        products_list.append(product_line_list)

        logging.info(f"products_list: {products_list}")

        if product_nrs[line_count].accessible_name == "":
            done = True
        else:
            line_count += 1
            # This is the header line, skip it

    
    return products_list, line_count

def create_orderline(dealer, worksheet_id, product_nr, product_amount, user, password):
    # Check if it nessesary to create a new driver for each call
    driver = webdriver.Chrome(options=options)
    actions = ActionChains(driver)
    
    create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"\n\n*****************************************************************************************")
    logging.info(f"Creating orderline: {dealer}, {worksheet_id}, {product_nr}, {product_amount} at {create_time}")

    try:
        # Navigate to the login page
        driver.get("https://auth.cac.dk/Account/Login")
        driver.set_window_size(1728, 1055)

        # Perform login actions

        try:
            driver.find_element(By.ID, "inputEmail").send_keys("TAthomas")
            driver.find_element(By.ID, "inputPassword").click()
            driver.find_element(By.ID, "inputPassword").send_keys("TAthomas77")
            driver.find_element(By.CSS_SELECTOR, ".btn").click()
        except Exception as e:
            logging.error(f": Login failed with exception: {e}")
            raise loginException("Login failed")
        
        # Open worksheet(Arbejdskort) overview
        #try:
        driver.find_element(By.LINK_TEXT, "Åben kundestyring").click()
        driver.find_elements(By.TAG_NAME, "sb-worksheet-list")
        
        # Validate that the worksheet exists
        worksheet = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[@class='font-bold' and text()='#36993 ']"))
        )
        worksheet.click()
        time.sleep(1)

        products_list, line_count = refresh_product_lines(driver)

        # Add new productline and autocompleate by TAB
        # The find_element(By.XPATH,'.//child-cell/input') is used to find the input field in the cell
        # othervise the the line is not autocompleated/saved
        products_list[line_count-1][0]['element'].find_element(By.XPATH,'.//child-cell/input').send_keys("8221965")
        products_list[line_count-1][0]['element'].find_element(By.XPATH,'.//child-cell/input').send_keys(Keys.TAB)

        # Reffresh the page to get the new productlines
        time.sleep(1)
        driver.refresh()
        time.sleep(1)
        products_list, line_count = refresh_product_lines(driver)
        time.sleep(1)

        # Append OilMat identifier to productdescription of new productline
        inner_element = products_list[line_count-2][1]['element'].find_element(By.XPATH, ".//div/div")
        driver.execute_script("arguments[0].innerText += ' -- OilMat: 000001';", inner_element)

        # Append OilMat identifier to productdescription of new productline
        #inner_element = products_list[line_count-2][5]['element'].find_element(By.XPATH, ".//numeric-cell-renderer/input")
        #driver.execute_script("arguments[0].innerText = '3';", inner_element)
        
        time.sleep(1)
        #products_list[line_count-2][4]['element'].find_element(By.XPATH,'//numeric-cell-renderer/input').send_keys(3)
        #products_list[line_count-2][4]['element'].find_element(By.XPATH,'.//numeric-cell-renderer/input').send_keys(Keys.TAB)
        # //*[@id="wrapper"]/div[2]/app-worksheet-root/div[1]/app-worksheet-view-v2/div[2]/div/div/div/div/worksheet-line-v2/ag-grid-angular/div/div[1]/div[2]/div[3]/div[1]/div/div[2]/div/div/div[19]/div[4]/numeric-cell-renderer/input
        time.sleep(1)
        
        try:
            time.sleep(1)  # Wait for the page to load
        
        
        except Exception as e:
            logging.error(f": Failed to open worksheet overview")
            raise openWorksheetException(f": Failed to open worksheet overview")
            worksheet_found = False


        time.sleep(10)  # Wait for the page to load
    except Exception as e:
        logging.error(f": Failed to open au2office: {e}")
        raise loginException("Login failed")
    
        
def main(argv):
   dealer =  argv[0] 
   worksheet_id=  argv[1] 
   product_nr =  argv[2] 
   product_amount =  argv[3] 
   user =  argv[4] 
   password =  argv[5] 

   create_orderline(dealer, worksheet_id, product_nr, product_amount,user,password)

if __name__ == "__main__":
   main(sys.argv[1:])