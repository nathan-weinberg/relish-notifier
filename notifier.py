import sys
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException 

from selenium_stealth import stealth
import keyring

STATUS_CHECK_SECONDS = 30
PLACED_STATUS = "Order Placed"
PREPARING_STATUS = "Preparing Your Order"
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
    if status not in [PLACED_STATUS, PREPARING_STATUS, ARRIVED_STATUS]:
        print(f"Got unexpected status: {status}")
    return status 


def checkLunchTime() -> str:
    ''' checks if it's lunch time or nah
          early lunch time is defined as before 11:30am
          on-time lunch time is defined as anywhere between 11:30am and Noon
          late lunch time is defined as anytime after Noon
    '''
    now = datetime.now()
    if (now.hour < 11) or (now.hour == 11 and now.minute < 30):
        return "EARLY"
    elif (now.hour >= 12):
        return "LATE"
    else:
        return "ON-TIME"


def main():

    # initialize webdriver
    print("Initializing webdriver...")
    br = initializeWebDriver()

    # relish login
    print("Logging into Relish...")
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
    print("Begin lunch status checking...")
    try:
        while True:
            lunchTime = checkLunchTime()
            if lunchTime == "EARLY":
                print("Checking Relish, but it's a little early for lunch... someone is hungry!")
            elif lunchTime == "LATE":
                print("Checking Relish, but it's a little late for lunch... might wanna talk to Shawn!")
            elif lunchTime == "ON-TIME":
                pass
            else:
                raise Exception("UNRECOGNIZED LUNCH TIME - PLEASE ENSURE THE SPACE-TIME CONTINUUM IS INTACT")

            status = checkOrderStatus(br)
            print(f"CURRENT RELISH STATUS REPORTS AS: '{status}'")
            if status == ARRIVED_STATUS:
                print("Order has arrived!")
                #send_slack()
                break
            print(f"Checking again in {STATUS_CHECK_SECONDS} seconds...")
            br.refresh()
            sleep(STATUS_CHECK_SECONDS)
    except KeyboardInterrupt:
        pass

    # exit
    sys.exit(0)

if __name__ == "__main__":
    main()
