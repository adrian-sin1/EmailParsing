import pandas as pd
import tkinter as tk
from tkinter import filedialog
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from automation import (
    login, handle_disclaimer, click_create_new_constituent,
    fill_form, click_next_step, fill_details,
    select_intake_method, click_create_casework, click_create_casework_from_home,
    click_home_button
)


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

    tk.Label(root, text="Username:").pack(pady=(10, 0))
    username_var = tk.StringVar()
    tk.Entry(root, textvariable=username_var, width=40).pack()

    tk.Label(root, text="Password:").pack(pady=(10, 0))
    password_var = tk.StringVar()
    tk.Entry(root, textvariable=password_var, show='*', width=40).pack()

    auto_click_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Automatically click 'Create Casework'", variable=auto_click_var).pack(pady=10)

    tk.Button(root, text="Start", command=submit, width=15).pack(pady=10)

    root.mainloop()
    return user_data


# === GUI Prompt for Login and Options ===
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
DRIVER_PATH = r"C:\Users\ASin\Documents\edgedriver_win64\msedgedriver.exe"
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
            click_next_step(driver, wait)
            click_next_step(driver, wait)

            if auto_click_create:
                click_create_casework(driver, wait)

                if click_home_button(driver, wait):
                    if wait_for_home_screen(driver, wait):
                        time.sleep(1)
                        click_create_casework_from_home(driver, wait)
                    else:
                        print("❌ Home page not detected after clicking Home button.")
                else:
                    print("❌ Failed to click Home button after creating casework.")
            else:
                print("🛑 Please click 'Create Casework' manually in the browser...")
                try:
                    WebDriverWait(driver, 60).until_not(
                        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Create Casework')]"))
                    )
                    print("✅ Detected that 'Create Casework' was clicked.")
                except:
                    print("⚠️ Timeout waiting for manual click.")

                # New: Click the Home button just like auto mode
                if click_home_button(driver, wait):
                    if wait_for_home_screen(driver, wait):
                        time.sleep(0.5)
                        print("🔁 Returning to Create Casework form for next entry...")
                        click_create_casework_from_home(driver, wait)
                    else:
                        print("❌ Home page not detected after clicking Home button.")
                else:
                    print("❌ Failed to click Home button after manual create.")

            print("✅ Entry processed\n")

        print("\n✅ All entries processed.")
    finally:
        print("🛑 Browser left open for inspection.")
        input("Press Enter to exit and close browser...")
        driver.quit()

if __name__ == "__main__":
    main()
