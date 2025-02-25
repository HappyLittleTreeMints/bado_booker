import time
import logging
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta


LEISURE_CENTRE_URL = (
    "https://antrimandnewtownabbey.legendonlineservices.co.uk/valley/account/login"
)
LOGIN_BUTTON_XPATH = "//button[span[text()='Login']]"
CLUB_XPATH = "//ul[@class='select2-results__options select2-results__options--nested']/li[text()='Valley']"
PREFERRED_COURTS = [
    "Court 5",
    "Court 6",
    "Court 7",
    "Court 8",
    "Court 1",
    "Court 2",
    "Court 3",
    "Court 4",
]


def setup_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Run in headless mode
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--incognito")  # Add incognito mode
    driver = webdriver.Chrome(options=options)  # Update path to chromedriver if needed
    logging.info("WebDriver initialized successfully.")
    return driver


def _select_court(driver):
    selects = driver.find_elements(By.TAG_NAME, "select")
    if len(selects) == 1:
        raise RuntimeError("It's joever, no courts available")
    court_dropdown = Select(driver.find_elements(By.TAG_NAME, "select")[1])
    court_options = [option.text for option in court_dropdown.options]
    for court in PREFERRED_COURTS:
        if court in court_options:
            court_dropdown.select_by_visible_text(court)
            logging.info(f"Selected {court}")
            return
        else:
            logging.info(f"{court} not available")
            continue


# Booking function
def book_court(email, password):
    driver = setup_driver()
    try:
        driver.get(LEISURE_CENTRE_URL)
        logging.info(f"Navigated to {LEISURE_CENTRE_URL}")

        # cookie_accept_button = WebDriverWait(driver, 3).until(
        #     EC.element_to_be_clickable(
        #         (By.XPATH, "//button[text()='I Do Not Accept Cookies']")
        #     )
        # )
        # cookie_accept_button.click()

        # Login
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH))
        )
        driver.find_element(By.ID, "account-login-email").send_keys(email)
        driver.find_element(By.ID, "account-login-password").send_keys(password)
        driver.find_element(By.XPATH, LOGIN_BUTTON_XPATH).click()
        logging.info("Attempting Login")

        # Click 'Make A Booking'
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(text(), 'Make A Booking')]")
            )
        ).click()

        # Club dropdown
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='search']"))
        ).click()

        driver.find_element(By.XPATH, CLUB_XPATH).click()

        # Category - RACQUET SPORTS BOOKINGS
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "booking-behaviour-option19"))
        ).click()

        # Activities - VLC Badminton OL
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "booking-activity-option152"))
        ).click()

        # View Timetable
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[span[text()='View Timetable']]")
            )
        ).click()

        # Calculate next sunday
        today = datetime.today()
        days_to_next_sunday = (
            (6 - today.weekday() % 7) if (6 - today.weekday() % 7) else 7
        )
        # Can do some manual testing by changing next_sunday
        next_sunday = (today + timedelta(days=days_to_next_sunday)).day
        logging.info(f"Next Sunday: {today.strftime('%Y-%m-%d')}")

        is_next_sunday_in_next_month = (
            today + timedelta(days=days_to_next_sunday)
        ).month != today.month

        # Zebra datepicker
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "unique-identifier-2"))
        ).click()

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "Zebra_DatePicker"))
        )
        if is_next_sunday_in_next_month:
            driver.find_element(
                By.XPATH,
                "//div[@class='Zebra_DatePicker']/table[@class='dp_header dp_actions']//td[@class='dp_next']",
            ).click()

        # Select correct date
        driver.find_element(
            By.XPATH,
            f"//div[@class='Zebra_DatePicker']/table[@class='dp_daypicker dp_body']//td[text()={next_sunday}]",
        ).click()

        # Wait for grid to load
        time.sleep(1)

        # Click 11:15 slot
        # Slots appear in a grid with a single row. 11:15 is the 4th child for weekends (first slot at 9am)
        driver.find_element(
            By.CSS_SELECTOR, "div.row div.row div.col-xl-4:nth-child(4)"
        ).click()

        # Wait for pop up
        time.sleep(1)

        # Will throw here if timeslot is clicked and there are no courts available
        _select_court(driver)

        # Add to basket or Buy now
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Buy now']"))
        ).click()

        # Basket Summary - continue button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "universal-basket-continue-button"))
        ).click()

        # Accept terms and conditions
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "InputCheckbox-0"))
        ).click()

        # Click continue again
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "universal-basket-continue-button"))
        ).click()

        time.sleep(10)
        logging.info("Booking complete")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        driver.quit()
        logging.info("Webdriver closed")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--email", required=True, help="Login email address")
    parser.add_argument("-p", "--password", required=True, help="Login password")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    try:
        book_court(args.email, args.password)
    except KeyboardInterrupt:
        logging.info("Script terminated by user")
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
