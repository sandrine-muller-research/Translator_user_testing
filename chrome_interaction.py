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
import copy
import requests

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

def get_github_files(owner, repo, path):
    # GitHub API endpoint for getting contents of a repository
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    # Send a GET request to the GitHub API
    response = requests.get(api_url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        contents = json.loads(response.text)
        
        # Extract file names
        file_names = [item['name'] for item in contents if item['type'] == 'file']
        
        return file_names
    else:
        print(f"Error: Unable to fetch repository contents. Status code: {response.status_code}")
        return None

def extract_statement_from_result_container(result_container):

    result_paths = result_container.find_element(By.XPATH, ".//*[contains(@class, '_pathView_')]")
    children = result_paths.find_elements(By.XPATH, "./*")
    formatted_paths = children[1].find_elements(By.XPATH, "./*")
    if len(children) == 4:
        statement_direct = formatted_paths[1].find_element(By.XPATH, ".//*[contains(@class, '_tableItem_')]").text.replace("\n"," ")
        # for the inferred part, we are currently choosing to remove the support edges 
        top_path_inferred_elements = formatted_paths[3].find_element(By.XPATH, ".//*[contains(@class, '_tableItem_')]").find_elements(By.XPATH, "./*")
        statement_indirect = ""
        statement_triple = []
        for top_path_inferred_element in top_path_inferred_elements:
            if 'rah-static' not in top_path_inferred_element.get_attribute("class"):
                statement_triple.append(top_path_inferred_element.text)
        statement_indirect = " ".join(statement_triple)
                
    return statement_direct,statement_indirect,statement_triple



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
    if result is not None:
        score = result.get('score')
        feedback = result.get('feedback')
    else:
        return None, None
    
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
        WebDriverWait(driver, timeout).until(EC.text_to_be_present_in_element_value((By.ID, "submit-status"), "submitted"))

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

    except TimeoutException:
        results_in = None
        print("Timed out waiting for results to come in.")

    if results_in is not None:
        
        escape_pressed = EscapePressed()
        user_test_rating_list = []
        
        # get last asset id:
        files_list = get_github_files("NCATSTranslator", "Tests", "test_assets")
        files_list = [f for f in files_list if "README" not in f]
        files_list = [f for f in files_list if ".tsv" not in f]
        asset_id_list = [int(i.replace('Asset_',"").replace('.json',"")) for i in files_list]
        cpt = 0
        
        while not escape_pressed.escape_pressed:
            try:
                button = WebDriverWait(driver, 300).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, '_accordionButton_') and contains(@class, '_open_')]")))
                # data_result_name = button.get_attribute('data-result-name')
                user_test_rating = copy.deepcopy(json_template)
                
                result_container = button.find_element(By.XPATH, "./..")
                result_score = result_container.find_element(By.XPATH, ".//*[contains(@class, '_scoreNum_')]").text
                # statement_direct,statement_indirect,statement_triple = extract_statement_from_result_container(result_container)

                result_paths = result_container.find_element(By.XPATH, ".//*[contains(@class, '_pathView_')]")
                children = result_paths.find_elements(By.XPATH, "./*")
                formatted_paths = children[1].find_elements(By.XPATH, "./*")
                if len(children) == 4:
                    cpt += 1
                    statement_direct = formatted_paths[1].find_element(By.XPATH, ".//*[contains(@class, '_tableItem_')]").text.replace("\n"," ")
                    # for the inferred part, we are currently choosing to remove the support edges 
                    top_path_inferred_elements = formatted_paths[3].find_element(By.XPATH, ".//*[contains(@class, '_tableItem_')]").find_elements(By.XPATH, "./*")
                    statement_indirect = ""
                    statement_triple = []
                    statement_triple_categories = []
                    statement_triple_CURIES = []
                    for top_path_inferred_element in top_path_inferred_elements:
                        print(top_path_inferred_element.get_attribute("class"))
                        if 'rah-static' not in top_path_inferred_element.get_attribute("class"):
                            triple_name = top_path_inferred_element.text
                            statement_triple.append(triple_name)
                            if ('nameContainer' in top_path_inferred_element.get_attribute("class")) or ('targetContainer' in top_path_inferred_element.get_attribute("class")):
                               statement_triple_categories.append(top_path_inferred_element.get_attribute("data-tooltip-id").replace(triple_name, "")) # THIS NEEDS TO BE FURTHER PARSED TO DIFFERENTIATE CATEGORY FROM ENTITY
                               statement_triple_CURIES.append(top_path_inferred_element.get_attribute("data-tooltip-id").replace(triple_name, ""))
                            else:
                                statement_triple_categories.append("--")
                                statement_triple_CURIES.append("--")

                    statement_indirect_categories = " ".join(statement_triple_categories)
                    statement_indirect_CURIES = " ".join(statement_triple_CURIES)

                    # fill json:
                    user_test_rating["id"] = 'Asset_' + str(max(asset_id_list)+cpt)
                    user_test_rating["input_id"] = statement_triple_CURIES[0]
                    user_test_rating["input_name"] = statement_triple[0]
                    user_test_rating["input_category"] = statement_triple_categories[0]
                    user_test_rating["predicate_id"] = statement_triple[1]
                    user_test_rating["predicate_name"] = statement_triple_CURIES[1]
                    user_test_rating["output_id"] = statement_triple_CURIES[2]
                    user_test_rating["output_name"] = statement_triple[2]
                    user_test_rating["output_category"] = statement_triple_categories[2]     
                
                score, feedback = get_nps_feedback(driver,'NPSpopup_1_general.js')
                button.click()
                
                if score == 0:      # never show   
                    user_test_rating["expected_output"] = "NeverShow"       
                    user_test_rating["name"] = user_test_rating["expected_output"] + statement_direct
                    user_test_rating["description"] = user_test_rating["name"]
                    user_test_rating["input_name"] = user_test_rating["name"]
                    
                if score == 10:      # Top answer      
                    user_test_rating["expected_output"] = "TopAnswer"       
                    user_test_rating["name"] = user_test_rating["expected_output"] + statement_direct
                    user_test_rating["description"] = user_test_rating["name"]
                    user_test_rating["input_name"] = user_test_rating["name"]

                user_test_rating_list.append(user_test_rating)
                
                file_name = user_test_rating["id"] + ".json"
                # save asset:
                script_path = os.path.dirname(os.path.abspath(__file__))
                results_folder = os.path.join(script_path, "testing results")
                if not os.path.exists(results_folder):
                    os.makedirs(results_folder)
                # Define the file path for "my_file.json"
                json_file_path = os.path.join(results_folder, file_name)

                # Write the dictionary to "my_file.json"
                with open(json_file_path, 'w') as json_file:
                    json.dump(user_test_rating, json_file)

                print(f"File 'my_file.json' has been created in the 'testing results' folder at: {json_file_path}")
                
            except TimeoutException:
                print("score and feedback not recorded.")
                
            
            escape_pressed = EscapePressed()
        
        
        WebDriverWait(driver, 3600).until(escape_pressed)  # Wait up to 1 hour
        
        
        



