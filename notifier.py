import sys
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException 

from selenium_stealth import stealth
import keyring

ARRIVED_STATUS = "Order Arrived"


def initializeWebDriver() -> webdriver.Chrome:
    '''	initializes Chrome webdriver
    '''

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        # stealth options to stop relish from knowing this is a bot
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        br = webdriver.Chrome(options=options)
        stealth(
            br,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        return br
    except WebDriverException:
        print("Invalid input data.")
        sys.exit(1)


def checkOrderStatus(br) -> str:
    ''' check order status
    '''
    label = WebDriverWait(br, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "schedule-card-label")))
    status = label.text
    return status 


def main():

    # initialize webdriver
    br = initializeWebDriver()

    # relish login
    br.get("https://relish.ezcater.com/schedule")
    sleep(5)

    username = WebDriverWait(br, 10).until(EC.presence_of_element_located((By.ID, "identity_email")))
    email_secret = keyring.get_password("relish-notifier", "EMAIL")
    username.send_keys(email_secret)
    button = br.find_element(By.NAME, "commit")
    button.click()

    # ezcater login
    password = WebDriverWait(br, 10).until(EC.presence_of_element_located((By.ID, "password")))
    password_secret = keyring.get_password("relish-notifier", "PASSWORD")
    password.send_keys(password_secret)
    button = br.find_element(By.NAME, "action")
    button.click()

    # dismiss popup (i know it's weird but truly this was the only thing that worked
    #                PRs welcome to do better)
    sleep(5)
    br.get("https://relish.ezcater.com/schedule")

    # check status
    while True:
        status = checkOrderStatus(br)
        print(f"CURRENT RELISH STATUS REPORTS AS: '{status}'")
        if status == ARRIVED_STATUS:
            print("Order has arrived!")
            #send_slack()
            break
        br.refresh()
        sleep(30)

    # exit
    sys.exit(0)

if __name__ == "__main__":
    main()
