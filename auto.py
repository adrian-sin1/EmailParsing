import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fuzzywuzzy import process

# === CONFIG keys, adjust as needed ===
CSV_FILE = "filtered_output.csv"
LOGIN_URL = "https://councilconnect.council.nyc.gov/login"
FORM_URL = "https://councilconnect.council.nyc.gov/casework/create"
USERNAME = "ASin@council.nyc.gov"
PASSWORD = "wfZZSbwGM6beoo3"
DRIVER_PATH = r"C:\Users\ASin\Documents\edgedriver_win64\msedgedriver.exe"

# Map step 1 fields
FIELD_STEP_1 = {
    "Name": "newConstituent.name",
    "Email": "newConstituent.contact_info.0.contact_data"
}

def login(driver, wait):
    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    time.sleep(30)
    wait.until(EC.url_changes(LOGIN_URL))
    print("✅ Logged in")

def start_new_case(driver, wait):
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create New Constituent')]"))).click()
    time.sleep(2)
    wait.until(EC.visibility_of_element_located((By.ID, "newConstituent.name")))
    print("✅ New Constituent form open")

def fill_step1(driver, wait, row):
    for col, field_id in FIELD_STEP_1.items():
        val = row.get(col, "")
        if pd.isna(val) or not val:
            continue
        fld = wait.until(EC.element_to_be_clickable((By.ID, field_id)))
        fld.clear()
        fld.send_keys(str(val))
    print("✅ Step 1 filled")

def get_valid_topics(driver, wait):
    # click dropdown to populate choices
    topic_btn = wait.until(EC.element_to_be_clickable((By.ID, "topic-select")))
    topic_btn.click()
    time.sleep(1)
    lis = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul[role='listbox'] li")))
    topics = [li.text.strip() for li in lis if li.text.strip()]
    # close dropdown
    topic_btn.send_keys(Keys.ESCAPE)
    print(f"🔍 Scraped {len(topics)} topics")
    return topics

def map_subject(subject, topics):
    if not subject or not isinstance(subject, str):
        return ""
    match, score = process.extractOne(subject, topics)
    print(f"🔍 '{subject}' → '{match}' (score={score})")
    return match if score >= 65 else ""

def fill_case_details(driver, wait, subject, body, valid_topics):
    mapped = map_subject(subject, valid_topics)
    if not mapped:
        print(f"⚠️ No close topic for '{subject}'")
        return False

    # open dropdown
    btn = wait.until(EC.element_to_be_clickable((By.ID, "topic-select")))
    btn.click()
    time.sleep(0.5)
    opt = wait.until(EC.element_to_be_clickable((By.XPATH, f"//li[normalize-space()='{mapped}']")))
    opt.click()
    print(f"✅ Chose topic: {mapped}")

    # fill body
    desc = wait.until(EC.presence_of_element_located((By.ID, "details")))
    desc.clear()
    desc.send_keys(body)
    print("✅ Body filled")
    return True

def main():
    df = pd.read_csv(CSV_FILE)
    service = Service(DRIVER_PATH)
    driver = webdriver.Edge(service=service)
    wait = WebDriverWait(driver, 20)

    try:
        login(driver, wait)

        for idx, row in df.iterrows():
            print(f"\n🚀 Processing entry {idx+1}/{len(df)}")
            driver.get(FORM_URL)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))

            start_new_case(driver, wait)
            fill_step1(driver, wait, row)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-pejez8'))).click()
            print("➡️ Moved to Case Details")

            time.sleep(2)
            valid_topics = get_valid_topics(driver, wait)
            success = fill_case_details(driver, wait, row.get("Subject", ""), row.get("Body", ""), valid_topics)

            if not success:
                print("❗ Skipping this entry due to mapping failure")

            time.sleep(1)

        print("\n✅ Done!")

    finally:
        input("🛑 Completed—all browser windows remain open for review.")

if __name__ == "__main__":
    main()
