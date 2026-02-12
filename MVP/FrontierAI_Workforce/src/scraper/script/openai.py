from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
from datetime import datetime
import os
import time

url = "https://openai.com/careers/search/";
company = "OpenAI";
today = datetime.now().strftime("%Y-%m-%d");

chrome_options = Options();
chrome_options.add_argument("--headless=new");
chrome_options.add_argument("--no-sandbox");
chrome_options.add_argument("--disable-dev-shm-usage");
chrome_options.add_argument("--window-size=1920,1080");
chrome_options.add_argument("--disable-blink-features=AutomationControlled");
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]);
chrome_options.add_experimental_option('useAutomationExtension', False);

driver = webdriver.Chrome(options=chrome_options);
jobs_data = [];

try:
    driver.get(url);
    
    time.sleep(5);
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);");
    time.sleep(2);
    driver.execute_script("window.scrollTo(0, 0);");
    time.sleep(1);
    
    all_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/careers/"]');
    
    for link in all_links:
        try:
            h2_elements = link.find_elements(By.TAG_NAME, 'h2');
            if not h2_elements:
                continue;
            
            position = h2_elements[0].text.strip();
            
            if not position:
                continue;
            
            location = "";
            try:
                spans = link.find_elements(By.XPATH, './span');
                if spans:
                    location = spans[-1].text.strip();
            except:
                pass;
            
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

output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'openai.csv');
os.makedirs(os.path.dirname(output_path), exist_ok=True);

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['company', 'position', 'location', 'date']);
    writer.writeheader();
    writer.writerows(jobs_data);

print(f"OpenAI: {len(jobs_data)} jobs found");
