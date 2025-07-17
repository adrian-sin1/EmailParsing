import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==== CONFIGURATION ====
CSV_FILE = "filtered_output.csv"  # make sure this is in the same folder as the script
FORM_URL = "https://councilconnect.council.nyc.gov/casework/create"

BROWSER = "edge"
DRIVER_PATH = r"C:\Users\ASin\Documents\msedgedriver.exe"  # ← UPDATE THIS!

# Map your CSV columns to form input fields (adjust IDs or names after inspecting the form)
FIELD_MAP = {
    "Name": "constituent_name",          # Update this to the actual ID or name in the form
    "Email": "constituent_email",        # Update accordingly
    "Sender": "constituent_phone",       # Optional: change or add more
    # Add more fields here if needed
}

def fill_form(driver, data):
    """Fills out the form with data from one CSV row."""
    for csv_col, field_id_or_name in FIELD_MAP.items():
        val = data.get(csv_col, "")
        if not val or pd.isna(val):
            continue

        try:
            # Try ID first
            input_field = driver.find_element(By.ID, field_id_or_name)
        except:
            try:
                # Try name as fallback
                input_field = driver.find_element(By.NAME, field_id_or_name)
            except:
                print(f"⚠️ Could not find field: {field_id_or_name}")
                continue

        input_field.clear()
        input_field.send_keys(val)

def main():
    df = pd.read_csv(CSV_FILE)

    # Launch correct browser driver
    if BROWSER == "chrome":
        driver = webdriver.Chrome(executable_path=DRIVER_PATH)
    elif BROWSER == "firefox":
        driver = webdriver.Firefox(executable_path=DRIVER_PATH)
    elif BROWSER == "edge":
        driver = webdriver.Edge(executable_path=DRIVER_PATH)
    else:
        raise ValueError("Unsupported browser")

    wait = WebDriverWait(driver, 10)

    for idx, row in df.iterrows():
        print(f"🚀 Submitting row {idx + 1}...")

        driver.get(FORM_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))

        # Fill form with row data
        fill_form(driver, row)

        # Click submit (adjust button selector if needed)
        try:
            submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
            submit_btn.click()
            print(f"✅ Submitted row {idx + 1}")
        except Exception as e:
            print(f"❌ Failed to submit row {idx + 1}: {e}")

        time.sleep(3)  # Wait for confirmation / avoid rate limits

    driver.quit()
    print("✅ All done! Browser closed.")

if __name__ == "__main__":
    main()
