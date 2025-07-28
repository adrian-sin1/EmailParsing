import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
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

FIELD_MAP_STEP_1 = {
    "Name": "newConstituent.name",
    "Email": "newConstituent.contact_info.0.contact_data"
}

def login(driver, wait):
    driver.get(LOGIN_URL)
    time.sleep(1)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    time.sleep(0.5)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    wait.until(EC.url_changes(LOGIN_URL))
    print("✅ Logged in")

def handle_disclaimer(driver, wait):
    print("⏳ Checking for disclaimer popup...")
    driver.save_screenshot("before_disclaimer.png")
    locators = [
        "//button[contains(text(),'Accept')]",
        "//button[contains(text(),'I Agree')]",
        "//button[contains(text(),'Continue')]",
        "//button[contains(text(),'OK')]",
        "//div[@aria-label='Disclaimer']//button"
    ]
    for xpath in locators:
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            time.sleep(0.5)
            btn.click()
            print(f"✅ Clicked disclaimer button: {xpath}")
            driver.save_screenshot("after_disclaimer.png")
            return
        except:
            continue

    # Check for disclaimer inside iframe
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in iframes:
            driver.switch_to.frame(frame)
            for xpath in locators:
                try:
                    btn = driver.find_element(By.XPATH, xpath)
                    btn.click()
                    driver.switch_to.default_content()
                    print("✅ Dismissed disclaimer in iframe")
                    return
                except:
                    continue
            driver.switch_to.default_content()
    except Exception as e:
        print(f"⚠️ Error checking iframes: {e}")
    print("ℹ️ No disclaimer popup found")

def click_create_new_constituent(driver, wait):
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create New Constituent')]"))).click()
        print("✅ Clicked 'Create New Constituent'")
    except Exception as e:
        print(f"❌ Could not click 'Create New Constituent': {e}")
        return False

    time.sleep(1)
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "newConstituent.name")))
        print("✅ Form appeared")
        return True
    except Exception as e:
        print(f"❌ Form did not appear: {e}")
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
            time.sleep(0.3)
            field.send_keys(str(value))
            print(f"✅ Filled '{col}'")
        except Exception as e:
            print(f"⚠️ Could not fill '{col}' in field '{field_id}': {e}")

def fill_details_react(driver, wait, body):
    try:
        textarea = wait.until(EC.element_to_be_clickable((By.ID, "details")))
        textarea.click()
        time.sleep(0.3)

        set_value_script = """
        const textarea = arguments[0];
        const value = arguments[1];
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
        nativeInputValueSetter.call(textarea, value);
        const event = new Event('input', { bubbles: true });
        textarea.dispatchEvent(event);
        """

        driver.execute_script(set_value_script, textarea, body)
        print("✅ Details field filled via JS")
        return True
    except Exception as e:
        print(f"❌ Failed filling details: {e}")
        driver.save_screenshot("error_details.png")
        return False

def click_next_step(driver, wait):
    try:
        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-pejez8')))
        time.sleep(0.5)
        next_btn.click()
        print("➡️ Clicked 'Next Step'")
    except Exception as e:
        print(f"⚠️ Could not click 'Next Step': {e}")

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

            # STEP 2 - fill 'Details' using React-friendly method
            wait.until(EC.visibility_of_element_located((By.ID, "details")))
            if not fill_details_react(driver, wait, row.get("Body", "")):
                print("⚠️ Skipped due to error filling details.")
                continue

            driver.save_screenshot(f"entry_{i + 1}_step2_filled.png")
            print("✅ Entry submitted\n")
            time.sleep(2)

        print("\n✅ All entries processed.")
    finally:
        print("🛑 Browser left open for inspection.")
        input("Press Enter to exit and close browser...")
        driver.quit()

if __name__ == "__main__":
    main()
