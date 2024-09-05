from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, JavascriptException
import signal
import sys
import os
import time
# import json
from bs4 import BeautifulSoup

def inject_html(driver):
    # Get the current page source
    current_html = driver.page_source

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(current_html, 'html.parser')

    # Add content to <head>
    head_tag = soup.head
    style_tag = soup.new_tag("style", id="new-content-nps")
    style_tag.string = """
                    #nps-popup {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.3);
                    z-index: 1000;
                    max-width: 300px;
                    width: 100%;
                }
                #nps-scale {
                    display: flex;
                    justify-content: space-between;
                    margin: 20px 0;
                }
                .nps-btn {
                    padding: 8px;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    background-color: white;
                    cursor: pointer;
                    font-size: 12px;
                }
                .nps-btn.selected {
                    background-color: #4285F4;
                    color: white;
                }
                #nps-feedback {
                    width: 100%;
                    height: 80px;
                    margin-bottom: 10px;
                    font-size: 14px;
                }
                #nps-submit {
                    display: block;
                    width: 100%;
                    padding: 10px;
                    background-color: #4285F4;
                    color: white;
                    border: none;
                    cursor: pointer;
                }"""
    head_tag.append(style_tag)

    # Add content to <body>
    body_tag = soup.body
    # new_div = soup.new_tag("div", id="new-content-nps")
    # new_div.string = """
    # """
    # body_tag.append(new_div)

    # Add a new <script> section
    script_tag = soup.new_tag("script")
    script_tag.string = """
            function showNPSPopup() {
            var popupHtml = `
                <div id="nps-popup">
                    <h2 style="font-size: 16px; margin-top: 0;">How likely are you to recommend us?</h2>
                    <div id="nps-scale">
                        ${[0,1,2,3,4,5,6,7,8,9,10].map(num => 
                            `<button class="nps-btn" data-score="${num}">${num}</button>`
                        ).join('')}
                    </div>
                    <textarea id="nps-feedback" placeholder="What's the primary reason for your score?"></textarea>
                    <button id="nps-submit">Submit</button>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', popupHtml);

            document.querySelectorAll('.nps-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.nps-btn').forEach(b => b.classList.remove('selected'));
                    this.classList.add('selected');
                });
            });

            document.getElementById('nps-submit').addEventListener('click', function() {
                var selectedBtn = document.querySelector('.nps-btn.selected');
                var score = selectedBtn ? selectedBtn.dataset.score : undefined;
                var feedback = document.getElementById('nps-feedback').value;
                if (score !== undefined) {
                    console.log('NPS Score:', score, 'Feedback:', feedback);
                    document.getElementById('nps-popup').remove();
                } else {
                    alert('Please select a score');
                }
            });
        }
    """
    body_tag.append(script_tag)

    # Update the page with the modified HTML
    modified_html = str(soup)
    # Clear the current page content
    driver.execute_script("document.body.innerHTML = '';")

    # Insert the new content
    driver.execute_script(f"document.documentElement.innerHTML = arguments[0];", modified_html)

def get_nps_feedback(driver):
    js_code = """
    function showNPSPopup() {
        return new Promise((resolve, reject) => {
            var popupHtml = `
            
                <div id="nps-popup" style="
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background-color: white;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 20px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    z-index: 9999;
                    max-width: 300px;
                ">
                    <h2 style="font-size: 16px; margin-top: 0;">How likely are you to recommend us?</h2>
                    <div id="nps-scale">
                        ${[0,1,2,3,4,5,6,7,8,9,10].map(num => 
                            `<button class="nps-btn" data-score="${num}">${num}</button>`
                        ).join('')}
                    </div>
                    <textarea id="nps-feedback" placeholder="(optionnal) What's the primary reason for your score?"></textarea>
                    <button id="nps-submit">Submit</button>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', popupHtml);

            document.querySelectorAll('.nps-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.nps-btn').forEach(b => b.classList.remove('selected'));
                    this.classList.add('selected');
                });
            });

            document.getElementById('nps-submit').addEventListener('click', function() {
                var selectedBtn = document.querySelector('.nps-btn.selected');
                var score = selectedBtn ? selectedBtn.dataset.score : undefined;
                var feedback = document.getElementById('nps-feedback').value;
                if (score !== undefined) {
                    document.getElementById('nps-popup').remove();
                    resolve({score: score, feedback: feedback});
                } else {
                    alert('Please select a score');
                }
            });
        });
    }
    return showNPSPopup();
    """
    
    # Execute the JavaScript and wait for the result
    result = driver.execute_script(js_code)
    
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

def text_form(driver, timeout=3600):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Translator URL Input Form</title>
        <script>
        function submitForm() {
            var input = document.getElementById('user-input').value;
            if (input.trim() !== '') {
                document.getElementById('result').textContent = 'Thank you!';
                document.getElementById('submit-status').value = 'submitted';
            } else {
                alert('Please enter some text before submitting.');
            }
        }
        </script>
    </head>
    <body>
        <h2>Enter your PK:</h2>
        <textarea id="user-input" rows="4" cols="50"></textarea><br><br>
        <button onclick="submitForm()">Submit</button>
        <p id="result"></p>
        <input type="hidden" id="submit-status">
    </body>
    </html>
    """

    # Load the HTML into the browser
    driver.get("data:text/html;charset=utf-8," + html)

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
        

    return """
    function createPopupSurvey() {
        // Remove existing survey if it exists
        var existingSurvey = document.getElementById('surveyPopup');
        if (existingSurvey) {
            existingSurvey.remove();
        }

        var surveyDiv = document.createElement('div');
        surveyDiv.id = 'surveyPopup';
        surveyDiv.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            max-width: 400px;
            width: 100%;
        `;
        surveyDiv.innerHTML = `
            <h2>Feedback Survey</h2>
            <p>How would you rate this result?</p>
            <div id="ratingContainer">
                <button class="ratingBtn" data-rating="1">1</button>
                <button class="ratingBtn" data-rating="2">2</button>
                <button class="ratingBtn" data-rating="3">3</button>
                <button class="ratingBtn" data-rating="4">4</button>
                <button class="ratingBtn" data-rating="5">5</button>
            </div>
            <textarea id="feedbackText" placeholder="Additional comments (optional)"></textarea>
            <button id="submitFeedback">Submit</button>
            <button id="closeSurvey">Close</button>
        `;
        document.body.appendChild(surveyDiv);

        document.querySelectorAll('.ratingBtn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.ratingBtn').forEach(b => b.style.backgroundColor = 'white');
                this.style.backgroundColor = '#4285F4';
                this.style.color = 'white';
            });
        });

        document.getElementById('submitFeedback').addEventListener('click', function() {
            var rating = document.querySelector('.ratingBtn[style*="background-color: rgb(66, 133, 244)"]')?.dataset.rating;
            var feedback = document.getElementById('feedbackText').value;
            console.log('Rating:', rating, 'Feedback:', feedback);
            // Here you would typically send this data to your server
            alert('Thank you for your feedback!');
            document.getElementById('surveyPopup').remove();
        });

        document.getElementById('closeSurvey').addEventListener('click', function() {
            document.getElementById('surveyPopup').remove();
        });
    }
    """

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)  # Register Ctrl+Z handler
    
    # Set up the WebDriver with JavaScript support
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-fullscreen")
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome(options=chrome_options)



    # Get query URL and navigate to it:
    Translator_results_url = text_form(driver, timeout=3600)
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
        
        # add_html_notification_to_button(driver,'general_rating_pop_up.html', 300 ,class_type)
        try:
            panel = WebDriverWait(driver, 3600).until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, '_accordionPanel_') and contains(@class, '_open')]")))
            # inject_html(driver)
            score, feedback = get_nps_feedback(driver)
            print("found")
        except TimeoutException:
            print("not found")
            
        # Wait for the Escape key to be pressed
        escape_pressed = EscapePressed()
        WebDriverWait(driver, 3600).until(escape_pressed)  # Wait up to 1 hour


