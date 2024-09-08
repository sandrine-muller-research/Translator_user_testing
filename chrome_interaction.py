from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, JavascriptException
import signal
import sys
import os
import time
import re
import json
from bs4 import BeautifulSoup

# def inject_html(driver,html_startup_file_path):
#     # Get the current page source
#     current_html = driver.page_source
    
#     html_content =  BeautifulSoup(html_startup_file_path, 'html.parser')

#     # Parse the HTML using BeautifulSoup
#     target_content = BeautifulSoup(current_html, 'html.parser')

#     # Add content to <head>
#     head_tag = target_content.head
#     style_tag = target_content.new_tag("style", id="new-content-nps")
#     style_tag.string = html_content.head
#     head_tag.append(style_tag)

#     # Add content to <body>
#     body_tag = target_content.body
#     # new_div = target_content.new_tag("div", id="new-content-nps")
#     # new_div.string = """
#     # """
#     # body_tag.append(new_div)

#     # Add a new <script> section
#     script_tag = target_content.new_tag("script")
#     script_tag.string = 
#     body_tag.append(script_tag)

#     # Update the page with the modified HTML
#     modified_html = str(target_content)
#     # Clear the current page content
#     driver.execute_script("document.body.innerHTML = '';")

#     # Insert the new content
#     driver.execute_script(f"document.documentElement.innerHTML = arguments[0];", modified_html)

def load_js_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            js_content = file.read()
            
        # Remove leading/trailing whitespace from each line and join
        js_content = '\n'.join(line.strip() for line in js_content.splitlines())
        
        # Optional: Remove empty lines
        js_content = re.sub(r'\n\s*\n', '\n', js_content)
        
        return js_content
    except FileNotFoundError:
        print(f"Error: JavaScript file not found at {file_path}")
        return None
    except IOError:
        print(f"Error: Unable to read JavaScript file at {file_path}")
        return None
    
def get_nps_feedback(driver,popup_js_filepath):
    
    abs_file_path = os.path.abspath(popup_js_filepath)
    js_code = load_js_file(abs_file_path)
    logs = driver.get_log('browser')
    for entry in logs:
        print(entry)
     
    # Execute the JavaScript and wait for the result
    try:
        result = driver.execute_script(js_code)
        # result = driver.execute_script("showNPSPopup();")
    except Exception as e:
        print(f"Could not show the pop up. An error occurred: {e}")
    
    # Extract score and feedback from the result
    score = result.get('score')
    feedback = result.get('feedback')
    
    return score, feedback

class EscapePressed:
    def __init__(self):
        self.escape_pressed = False

    def __call__(self, driver):
        try:
            self.escape_pressed = driver.execute_script("""
                if (!window.escapeListener) {
                    window.escapeListener = function(e) {
                        if (e.key === 'Escape') {
                            window.escapePressed = true;
                        }
                    };
                    document.addEventListener('keydown', window.escapeListener);
                }
                return window.escapePressed === true;
            """)
        except Exception as e:
            print(f"Error checking for Escape key: {e}")
        return self.escape_pressed

def signal_handler(signum, frame):
    if signum == signal.SIGINT:
        print("\nCtrl+C or Ctrl+Z detected. Exiting...")
        driver.quit()
        sys.exit(0)


def load_html_file(driver, file_path):
    # Get the absolute path of the HTML file
    abs_file_path = os.path.abspath(file_path)
    
    # Create a file URL
    file_url = f"file://{abs_file_path}"
    
    # Load the HTML file in the browser
    driver.get(file_url)
    
    # Wait for the body to be present to ensure the page has loaded
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))


def text_form(driver, html_startup_file_path, timeout=3600):

    try:
        # Load the HTML file
        load_html_file(driver, html_startup_file_path)
    except Exception as e:
        print(f"An error occurred: {e}")

    try:
        # Wait for the form to be submitted
        WebDriverWait(driver, timeout).until(
            EC.text_to_be_present_in_element_value((By.ID, "submit-status"), "submitted")
        )

        # Get the user input
        user_input = driver.find_element(By.ID, "user-input").get_attribute("value")
        return user_input

    except TimeoutException:
        print(f"Form was not submitted within {timeout} seconds.")
        return None
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
        

if __name__ == "__main__":
    
    # Load json file template:
    with open('asset_template.json', 'r') as f:
        json_template = json.load(f)
    
    
    signal.signal(signal.SIGINT, signal_handler)  # Register Ctrl+Z handler
    
    # Set up the WebDriver with JavaScript support
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-fullscreen")
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--disable-search-engine-choice-screen")
    driver = webdriver.Chrome(options=chrome_options)

    # Get query URL and navigate to it:
    Translator_results_url = None
    while Translator_results_url is None:
        Translator_results_url = text_form(driver, 'start_up.html', timeout=3600)
        
    try:
        driver.get(Translator_results_url)
    except Exception as e:
        print(f"Could not go to Translator URL page. An error occurred: {e}")
    
    # Wait for results to be in:
    class_type = 'resultsTable'
    results_xpath = f"//*[contains(@class, '{class_type}')]"
    try:
        results_in = WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.XPATH, results_xpath)))
        print("Results are in.")
        # query_elements = WebDriverWait(driver, 300).until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(@class, 'resultsHeader')]//h6")))
        # if "What drugs may treat conditions related to" in query_elements[0].text:
        #     json_template[""]
    except TimeoutException:
        results_in = None
        print("Timed out waiting for results to come in.")

    if results_in is not None:
        
        escape_pressed = EscapePressed()
        
        while not escape_pressed.escape_pressed:
            try:
                button = WebDriverWait(driver, 300).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, '_accordionButton_') and contains(@class, '_open_')]")))
                data_result_name = button.get_attribute('data-result-name')
                score, feedback = get_nps_feedback(driver,'NPSpopup_1_general.js')
                
                parent = button.find_element(By.XPATH, "./..")
                # children = parent.find_elements(By.XPATH, ".//*[contains(@class, '_tableItem_1maym_13')]")
                children = WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.XPATH, ".//*[contains(@class, '_tableItem_1maym_13')]")))
                name_container = WebDriverWait(children, 10).until(EC.presence_of_element_located((By.XPATH, ".//*[contains(@class, '_nameContainer_1e6to_9')]")))
                tooltip_element = WebDriverWait(name_container, 300).until( EC.presence_of_element_located((By.XPATH, ".//*[@data-tooltip-id]")))
                subject = tooltip_element.get_attribute("data-tooltip-id")

                
            # TO DO:
            # For each accordion button : 
            #     get the parent class P
            #     get all child of P that is of class="_tableItem_1maym_13"
            #     SUBJECT =  first item of class=" _nameContainer_1e6to_9" and extract "data-tootip-id" text
            #     Predicate =  first item of class=" _pathContainer_1e6to_9", get the child of class="_pathLabel_1rdsx_37"
            #     OBJECT =  third item of class=" _nameContainer_1e6to_9" and extract "data-tootip-id" text
                
                
            except TimeoutException:
                print("score and feedback not recorded.")
                
            print(score)
            
            escape_pressed = EscapePressed()
        
        
        WebDriverWait(driver, 3600).until(escape_pressed)  # Wait up to 1 hour
        
        
        



