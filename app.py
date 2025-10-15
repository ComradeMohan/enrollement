# app.py
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Function to send email notification
def send_email_notification(course_name, receiver_email, status):
    sender_email = os.getenv("SENDER_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")
    subject = f"Course {course_name} Status"
    body = f"The course {course_name} {status}. Please check the website for details."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return f"Notification email sent to {receiver_email}"
    except Exception as e:
        return f"Failed to send email: {e}"

# Function to set up Selenium WebDriver
def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Use remote WebDriver (e.g., BrowserStack or local Selenium Grid)
    driver = webdriver.Chrome(options=options)  # Assumes a Selenium Grid or Docker setup
    return driver

# Function to login to the website
def login(driver, username, password):
    driver.get("https://arms.sse.saveetha.com")
    time.sleep(2)
    username_field = driver.find_element(By.ID, "txtusername")
    password_field = driver.find_element(By.ID, "txtpassword")
    login_button = driver.find_element(By.ID, "btnlogin")
    username_field.send_keys(username)
    password_field.send_keys(password)
    login_button.click()
    time.sleep(1)

# Function to go to enrollment page
def go_to_enrollment_page(driver):
    driver.get("https://arms.sse.saveetha.com/StudentPortal/Enrollment.aspx")
    time.sleep(1)

# Function to select slot
def select_slot(driver, slot_letter):
    slot_number = ord(slot_letter.upper()) - 64
    slot_dropdown = Select(driver.find_element(By.ID, "cphbody_ddlslot"))
    slot_dropdown.select_by_value(str(slot_number))
    time.sleep(1)

# Function to check for course
def check_for_course(driver, course_name):
    time.sleep(1)
    course_found = False
    rows = driver.find_elements(By.CSS_SELECTOR, "#tbltbodyslota tr")

    for row in rows:
        labels = row.find_elements(By.TAG_NAME, "label")
        badges = row.find_elements(By.CLASS_NAME, "badge")
        for label, badge in zip(labels, badges):
            if course_name in label.text:
                vacancies = int(badge.text)
                if vacancies > 0:
                    radio_button = row.find_element(By.CSS_SELECTOR, "input[type='radio']")
                    radio_button.click()
                    return f"Course {course_name} selected. Vacancies: {vacancies}", True
                else:
                    return f"Course {course_name} found but no vacancies.", False
    return f"Course {course_name} not found.", False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_course():
    course_name = request.form['course_code']
    slot_letter = request.form['slot_letter']
    receiver_email = request.form['email']
    username = request.form['username']
    password = request.form['password']

    driver = setup_driver()
    try:
        login(driver, username, password)
        go_to_enrollment_page(driver)
        select_slot(driver, slot_letter)
        result, success = check_for_course(driver, course_name)
        email_status = send_email_notification(course_name, receiver_email, result)
        return render_template('result.html', result=result, email_status=email_status)
    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
