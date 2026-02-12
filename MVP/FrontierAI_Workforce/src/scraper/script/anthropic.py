from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
from datetime import datetime
import os
import time

url = "https://www.anthropic.com/careers/jobs";
company = "Anthropic";
today = datetime.now().strftime("%Y-%m-%d");

chrome_options = Options();
chrome_options.add_argument("--headless");
chrome_options.add_argument("--no-sandbox");
chrome_options.add_argument("--disable-dev-shm-usage");
chrome_options.add_argument("--window-size=1920,1080");

driver = webdriver.Chrome(options=chrome_options);
jobs_data = [];

try:
    driver.get(url);
    
    wait = WebDriverWait(driver, 10);
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'section[class*="jobList"]')));
    
    time.sleep(2);
    
    checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]');
    for checkbox in checkboxes:
        try:
            if not checkbox.is_selected():
                driver.execute_script("arguments[0].click();", checkbox);
                time.sleep(0.5);
        except:
            pass;
    
    time.sleep(2);
    
    job_items = driver.find_elements(By.CSS_SELECTOR, 'a[class*="jobItem"]');
    
    for job in job_items:
        try:
            position_elem = job.find_element(By.CSS_SELECTOR, 'div[class*="jobRole"] p');
            position = position_elem.text.strip();
            
            location = "";
            try:
                location_elem = job.find_element(By.CSS_SELECTOR, 'div[class*="jobLocation"] p');
                location = location_elem.text.strip();
            except:
                pass;
            
            if position:
                jobs_data.append({
                    'company': company,
                    'position': position,
                    'location': location,
                    'date': today
                });
        except Exception as e:
            continue;
    
finally:
    driver.quit();

output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'anthropic.csv');
os.makedirs(os.path.dirname(output_path), exist_ok=True);

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['company', 'position', 'location', 'date']);
    writer.writeheader();
    writer.writerows(jobs_data);

print(f"Anthropic: {len(jobs_data)} jobs found");
