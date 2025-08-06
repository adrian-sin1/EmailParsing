import pandas as pd
import tkinter as tk
from tkinter import filedialog
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
from datetime import datetime
import os
import sys




from automation import (
    login, handle_disclaimer, click_create_new_constituent,
    fill_form, click_next_step, fill_details,
    select_intake_method, click_create_casework, click_create_casework_from_home,
    click_home_button
)

# === GUI Prompt for Login and Options ===
def get_user_inputs():
    user_data = {}

    def submit():
        user_data["username"] = username_var.get()
        user_data["password"] = password_var.get()
        user_data["auto_click"] = auto_click_var.get()
        root.destroy()

    root = tk.Tk()
    root.title("Casework Automation Setup")
    root.geometry("400x220")
    root.attributes('-topmost', True)

    tk.Label(root, text="Council ID:").pack(pady=(10, 0))
    username_var = tk.StringVar()
    tk.Entry(root, textvariable=username_var, width=40).pack()

    tk.Label(root, text="Password:").pack(pady=(10, 0))
    password_var = tk.StringVar()
    tk.Entry(root, textvariable=password_var, show='*', width=40).pack()

    auto_click_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Automatically click 'Save'", variable=auto_click_var).pack(pady=10)

    tk.Button(root, text="Start", command=submit, width=15).pack(pady=10)

    root.mainloop()
    return user_data


def set_opened_at_now(driver):
    from datetime import datetime

    now = datetime.now()
    formatted_datetime = now.strftime("%Y-%m-%dT%H:%M")  # e.g., 2025-07-29T15:25

    opened_at_input = driver.find_element(By.ID, "opened_at")

    # Set value and dispatch input event
    driver.execute_script("""
        const input = arguments[0];
        const value = arguments[1];
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(input, value);
        input.dispatchEvent(new Event('input', { bubbles: true }));
    """, opened_at_input, formatted_datetime)

    print(f"🕒 Set 'Opened At' to current datetime: {formatted_datetime}")




user_inputs = get_user_inputs()
USERNAME = user_inputs["username"]
PASSWORD = user_inputs["password"]
auto_click_create = user_inputs["auto_click"]
print(f"✅ Auto click create casework is set to: {auto_click_create}")


# === File picker ===
def get_csv_file():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    print("Opening file picker dialog...")
    file_path = filedialog.askopenfilename(
        title="Select CSV File",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    root.destroy()
    print(f"File selected: {file_path}")
    return file_path

# === Utility Functions ===
def element_exists(driver, xpath):
    try:
        driver.find_element(By.XPATH, xpath)
        return True
    except NoSuchElementException:
        return False

def wait_for_home_screen(driver, wait, timeout=120):
    print("⏮ Waiting for return to Home screen...")
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(),'Create Casework')]"))
        )
        print("✅ Detected 'Create Casework' on home screen.")
        return True
    except Exception as e:
        print("❌ Timed out waiting for Home screen.")
        return False

# === Config ===

def get_driver_path(filename):
    if getattr(sys, 'frozen', False):  # if running as compiled exe
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

DRIVER_PATH = get_driver_path("msedgedriver.exe")

LOGIN_URL = "https://councilconnect.council.nyc.gov/login"
FORM_URL = "https://councilconnect.council.nyc.gov/casework/create"

FIELD_MAP_STEP_1 = {
    "Name": "newConstituent.name",
    "Email": "newConstituent.contact_info.0.contact_data"
}

# === Main Function ===
def main():
    CSV_FILE = get_csv_file()
    if not CSV_FILE:
        print("❌ No file selected. Exiting.")
        return

    df = pd.read_csv(CSV_FILE)
    service = Service(DRIVER_PATH)
    driver = webdriver.Edge(service=service)
    wait = WebDriverWait(driver, 30)

    try:
        login(driver, wait, LOGIN_URL, USERNAME, PASSWORD)
        handle_disclaimer(driver, wait)

        for i, row in df.iterrows():
            print(f"\n🚀 Submitting entry {i + 1}/{len(df)}")
            driver.get(FORM_URL)
            wait.until(lambda d: d.find_element(By.TAG_NAME, "form"))

            if not click_create_new_constituent(driver, wait):
                print("⏭ Skipping entry: form not opened.")
                continue

            fill_form(driver, row, FIELD_MAP_STEP_1)
            click_next_step(driver, wait)

            wait.until(lambda d: d.find_element(By.ID, "details"))
            if not fill_details(driver, wait, row.get("Reply", "")):
                print("⚠️ Skipped due to error filling details.")
                continue

            click_next_step(driver, wait)
            select_intake_method(driver, wait, "Emailed")
            set_opened_at_now(driver)
            time.sleep(1)

            click_next_step(driver, wait)
            click_next_step(driver, wait)

            if auto_click_create:
                try:
                    print("⏳ Waiting for 'Create Casework' button to appear...")
                    wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Create Casework')]")))
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create Casework')]")))
                    click_create_casework(driver, wait)
                    time.sleep(1)  # short delay to let form complete
                    print("✅ Casework created. Moving to next person...\n")
                except Exception as e:
                    print(f"❌ Auto-click failed: {e}")
                continue


            else:
                print("🛑 Please click 'Create Casework' manually in the browser...")

                # Wait until user submits or skips
                home_screen_loaded = False
                print("⌛ Waiting for user to either submit OR skip (manually return to Home)...")

                while True:
                    # Check if form was submitted (buttons gone)
                    if not element_exists(driver, "//button[contains(text(), 'Create Casework')]") and \
                       not element_exists(driver, "//button[contains(text(), 'Next Step')]"):
                        print("✅ Form submitted — detected button disappearance.")
                        break

                    # Check if user went back to Home screen
                    if element_exists(driver, "//h2[contains(text(),'Create Casework')]"):
                        print("⏩ User skipped form — detected return to Home screen.")
                        home_screen_loaded = True
                        time.sleep(2)
                        break

                    time.sleep(4)

                    

                # Proceed to next entry
                

        print("\n✅ All entries processed.")
    finally:
        print("🛑 Browser left open for inspection.")
        input("Press Enter to exit and close browser...")
        driver.quit()

if __name__ == "__main__":
    main()
