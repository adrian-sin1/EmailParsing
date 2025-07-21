import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === CONFIGURATION ===
CSV_FILE = "filtered_output.csv"
LOGIN_URL = "https://councilconnect.council.nyc.gov/login"
FORM_URL = "https://councilconnect.council.nyc.gov/casework/create"
USERNAME = "ASin@council.nyc.gov"
PASSWORD = "wfZZSbwGM6beoo3"
DRIVER_PATH = r"C:\Users\ASin\Documents\edgedriver_win64\msedgedriver.exe"

# === FIELD MAPS ===
FIELD_MAP_STEP_1 = {
    "Name": "newConstituent.name"
}
FIELD_MAP_STEP_2 = {
    "Subject": "topic-select",
    "Body": "details"
}

def login(driver, wait):
    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    wait.until(EC.url_changes(LOGIN_URL))
    print("✅ Logged in")

def handle_disclaimer(driver, wait):
    try:
        accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]")))
        accept_btn.click()
        print("✅ Dismissed disclaimer popup")
    except:
        print("ℹ️ No disclaimer popup found")

def click_create_new_constituent(driver, wait):
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create New Constituent')]"))).click()
        print("✅ Clicked 'Create New Constituent'")
    except Exception as e:
        print(f"❌ Failed to click 'Create New Constituent': {e}")
        return False

    time.sleep(2)
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "newConstituent.name")))
        print("✅ Form appeared")
        return True
    except Exception as e:
        print(f"❌ Form did not appear after clicking: {e}")
        driver.save_screenshot("form_not_appeared.png")
        return False

def fill_form(driver, row, field_map):
    for col, field_id in field_map.items():
        value = row.get(col, "")
        if pd.isna(value) or not value:
            continue
        try:
            field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, field_id)))
            field.clear()
            time.sleep(0.5)
            field.send_keys(str(value))
            print(f"✅ Filled '{col}'")
            if field_id == "topic-select":
                time.sleep(1)
                field.send_keys(Keys.DOWN)
                field.send_keys(Keys.RETURN)
                print("➡️ Selected autocomplete topic")
        except Exception as e:
            print(f"⚠️ Could not fill '{field_id}': {e}")

def click_next_step(driver, wait):
    try:
        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-pejez8')))
        next_btn.click()
        print("➡️ Clicked 'Next Step'")
    except Exception as e:
        print(f"⚠️ Failed to click 'Next Step': {e}")

def main():
    df = pd.read_csv(CSV_FILE)
    service = Service(DRIVER_PATH)
    driver = webdriver.Edge(service=service)
    wait = WebDriverWait(driver, 30)

    try:
        login(driver, wait)
        handle_disclaimer(driver, wait)

        for i, row in df.iterrows():
            print(f"\n🚀 Submitting entry {i + 1}/{len(df)}")
            driver.get(FORM_URL)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))

            if not click_create_new_constituent(driver, wait):
                print("⏭ Skipping entry: form not opened.")
                continue

            fill_form(driver, row, FIELD_MAP_STEP_1)
            click_next_step(driver, wait)

            # STEP 2 - Casework Details
            wait.until(EC.visibility_of_element_located((By.ID, "details")))
            fill_form(driver, row, FIELD_MAP_STEP_2)
            driver.save_screenshot(f"entry_{i+1}_step2_filled.png")
            print("✅ Step 2 filled")

            time.sleep(2)  # Pause between entries

        print("\n✅ All entries processed.")

    finally:
        print("🛑 Leaving browser open for inspection.")
        input() 

if __name__ == "__main__":
    main()
