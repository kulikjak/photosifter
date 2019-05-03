#!__venv__/bin/python3.7

import argparse
import os
import sys
import pickle
import time
import json

try:
    from selenium import webdriver
except ImportError:
    print("Cannot import selenium package. Is it installed?")
    print("To run this script you will also need chrome webdriver.")
    print("Download it here: http://chromedriver.chromium.org/downloads")
    sys.exit(100)

from selenium.common.exceptions import UnableToSetCookieException
from selenium.common.exceptions import WebDriverException


# Delete button title html attribute
DELETE_BUTTON_TITLE = "Smazat"
# Text inside the confirmation buttn
CONFIRMATION_TEXT = "Přesunout do koše"

# Google photos server address
SERVER_ADDRESS = 'https://photos.google.com/'

JS_CLICK_DELETE = f"""
node = document.querySelector('[title="{DELETE_BUTTON_TITLE}"]');
if (node == null)
  return false;
node.click();
return true;
"""

JS_CONFIRM_DELETE = f"""
found = false;
for (const span of document.querySelectorAll("span")) {{
  if (span.textContent.includes("{CONFIRMATION_TEXT}")) {{
    span.click();
    found = true;
  }}
}}
return found;
"""


def init_driver():
    """Return initialized and logged-in driver or None if error occured."""

    dir_path = os.path.dirname(os.path.realpath(__file__))
    driver_location = os.path.join(dir_path, 'chromedriver')
    try:
        driver = webdriver.Chrome(executable_path=driver_location)
    except WebDriverException as err:
        print(f"Cannot start the chrome driver.\n{err}", end="")
        return None

    driver.get(SERVER_ADDRESS)

    # Load previously saved cookie file if it exists
    cookies_success = False
    try:
        print("Loading cookies ...", end="")
        with open("cookies.pkl", "rb") as infile:
            cookies = pickle.load(infile)
            for cookie in cookies:
                driver.add_cookie(cookie)
        cookies_success = True
        print(" ok")
    except FileNotFoundError as err:
        print(" skipped")
    except IOError as err:
        print(f" err (IOError)\n Reason: {err}")
    except (EOFError, pickle.UnpicklingError) as err:
        print(f" err (file corrupted)\n Reason: {err}")
    except UnableToSetCookieException as err:
        print(f"Unexpected error occured:\n{err}")

    if cookies_success:
        driver.get(SERVER_ADDRESS)
        if driver.current_url != SERVER_ADDRESS:
            print("Loaded cookies are not enough to log into Google Photos")
            cookies_success = False

    if not cookies_success:
        input("Please, login into your google photos and press any key.")
        driver.get(SERVER_ADDRESS)
        if driver.current_url != SERVER_ADDRESS:
            print("Unable to login into the Google Photos")
            # We can do nothing more here
            driver.exit()
            return None

    # Save cookies for a future use (must be logged in here)
    with open("cookies.pkl", "wb") as file:
        pickle.dump(driver.get_cookies(), file)

    return driver


def delete_images(driver, url_list):
    """Delete Google Photo images from given urls"""

    for url in url_list:

        # Load page with current photograph
        try:
            driver.get(url)
        except WebDriverException as err:
            print(f"Error during loading of '{url}'\n{err}")

        # Confirm that something else is not being deleted
        if driver.current_url != url:
            # This should never happen
            print("Cannot get to given url.")
            continue

        # Click the delete button
        # Webpage is fully loaded now and so this element should already exist
        success = driver.execute_script(JS_CLICK_DELETE)
        if not success:
            # check if this photo was already deleted
            if "Error 404" in driver.title:
                print("This photo was probably already deleted.")
            else:
                print("Cannot locate delete button.")
            continue

        attempts = 12
        # This can take a little while to load so try it multiple times
        for _ in range(attempts):
            success = driver.execute_script(JS_CONFIRM_DELETE)
            if success:
                break
            time.sleep(0.25)
        else:
            print(f"Could not locate confirm box after {attempts} attempts.")
            continue


def test_deleted(driver, url_list):
    """Return images that are still not deleted."""

    # First load something that is definitely not current photo
    driver.get(SERVER_ADDRESS)

    problematic = []
    for url in url_list:
        try:
            driver.get(url)
        except WebDriverException as err:
            print(f"Error during loading of '{url}'\n{err}")

        # Deleted photos will have 404 error in the page title
        if "Error 404" not in driver.title:
            problematic.append(url)
    return problematic


def main():

    parser = argparse.ArgumentParser(
        description="Delete images from Google Photos.")
    parser.add_argument("-f", "--file",
        help="Json file with list of urls.")
    parser.add_argument("-u", "--url", action="append", default=[],
        help="Additional Google photo image url (can have multiple).")
    args = parser.parse_args()

    if args.file is None and not args.url:
        parser.error('Either --file or atleast one --url is required.')

    file_data = []
    if args.file:
        try:
            with open(args.file, "r") as infile:
                file_data = json.load(infile)
        except (IOError, json.decoder.JSONDecodeError) as err:
            print(f"Cannot read given file\n Reason: {err}")
            sys.exit(1)

    url_list = args.url + file_data
    if not url_list:
        print("No urls to process.")
        sys.exit(1)

    driver = init_driver()
    if driver is None:
        sys.exit(1)

    print("\nStarting main delete loop")
    try:
        delete_images(driver, url_list)
        problematic = test_deleted(driver, url_list)
        if problematic:
            print("Several photos could not be deleted. Retrying...")
            delete_images(driver, problematic)
            problematic = test_deleted(driver, problematic)

            if problematic:
                print("Cannot delete some photos even after one retry.")
                for item in problematic:
                    print(f"  {item}")

    except BaseException:
        # No matter what, always close the driver window.
        driver.quit()
        raise

    print("Done")
    driver.quit()


if __name__ == "__main__":
    main()