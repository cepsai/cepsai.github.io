from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
from datetime import datetime
import os
import time

url = "https://job-boards.greenhouse.io/deepmind";
company = "DeepMind";
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
    page = 1;
    
    while True:
        page_url = f"{url}?page={page}" if page > 1 else url;
        driver.get(page_url);
        
        wait = WebDriverWait(driver, 10);
        
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/jobs/"]')));
        except:
            break;
        
        time.sleep(2);
        
        job_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/jobs/"]');
        
        if not job_links:
            break;
        
        page_jobs = 0;
        
        for link in job_links:
            try:
                paragraphs = link.find_elements(By.TAG_NAME, 'p');
                
                if len(paragraphs) < 2:
                    continue;
                
                position = paragraphs[0].text.strip();
                location = paragraphs[1].text.strip();
                
                if position:
                    jobs_data.append({
                        'company': company,
                        'position': position,
                        'location': location,
                        'date': today
                    });
                    page_jobs += 1;
            except Exception as e:
                continue;
        
        if page_jobs == 0:
            break;
        
        page += 1;
    
finally:
    driver.quit();

output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'google.csv');
os.makedirs(os.path.dirname(output_path), exist_ok=True);

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['company', 'position', 'location', 'date']);
    writer.writeheader();
    writer.writerows(jobs_data);

print(f"Google: {len(jobs_data)} jobs found");
