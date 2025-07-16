# pyright: reportUnusedCallResult=false
import argparse
import subprocess
import sys
from time import sleep
import logging

from dataclasses import dataclass
from enum import StrEnum

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from selenium_stealth import stealth
import keyring

LOG_LEVELS = ["WARNING", "INFO", "DEBUG"]
LOG = logging.getLogger("relish")


class OrderStatus(StrEnum):
    PLACED = "Order Placed"
    PREPARING = "Preparing Your Order"
    ARRIVED = "Order Arrived"
    UNKNOWN = "Unknown"

    @classmethod
    def textToStatus(cls, text: str) -> "OrderStatus":
        for status in cls:
            if str(status) == text:
                return status

        raise KeyError


@dataclass
class Args:
    headless: bool = True
    extensions: bool = True
    interval: int = 30
    once: bool = False
    verbose: int = 0
    page_timeout: int = 10
    command: str | None = None

    def __post_init__(self):
        if self.verbose < 0 or self.verbose > len(LOG_LEVELS) - 1:
            self.verbose = len(LOG_LEVELS) - 1


@dataclass
class Credentials:
    username: str
    password: str


class Notifier:
    headless: bool = True
    extensions: bool = True
    pageTimeout: int = 10
    loginUrl: str = "https://relish.ezcater.com/schedule"
    br: webdriver.Chrome
    credentials: Credentials

    def __init__(
        self,
        credentials: Credentials,
        headless: bool | None = None,
        extensions: bool | None = None,
        pageTimeout: int | None = None,
    ):
        self.credentials = credentials

        if headless is not None:
            self.headless = headless
        if extensions is not None:
            self.extensions = extensions
        if pageTimeout is not None:
            self.pageTimeout = pageTimeout

        self.initializeWebDriver()

    def close(self):
        self.br.quit()

    def initializeWebDriver(self):
        """initializes Chrome webdriver"""

        chromeopts = webdriver.ChromeOptions()
        if self.headless:
            chromeopts.add_argument("--headless=new")

        if not self.extensions:
            chromeopts.add_argument("--disable-extensions")

        chromeopts.add_experimental_option("excludeSwitches", ["enable-automation"])
        chromeopts.add_experimental_option("useAutomationExtension", False)
        self.br = webdriver.Chrome(options=chromeopts)
        self.br.set_page_load_timeout(self.pageTimeout)

        # stealth options to stop relish from knowing this is a bot
        stealth(
            self.br,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

    def login(self):
        LOG.debug("logging in")

        self.br.get(self.loginUrl)
        self.waitAndSubmit("identity_email", "commit", self.credentials.username)
        self.waitAndSubmit("password", "action", data=self.credentials.password)

    def checkOrderStatus(self) -> OrderStatus:
        """check order status"""
        LOG.debug("check order status")

        try:
            label = WebDriverWait(self.br, self.pageTimeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "schedule-card-label"))
            )
        except TimeoutException:
            LOG.warning("timeout waiting for order status")
            return OrderStatus.UNKNOWN

        try:
            status = OrderStatus.textToStatus(label.text)
        except KeyError:
            LOG.warning(f"unknown order status: {label.text}")
            return OrderStatus.UNKNOWN

        return status

    def waitAndSubmit(self, element_id: str, button_name: str, data: str):
        LOG.debug(f"wait for {element_id} before clicking {button_name}")

        field = WebDriverWait(self.br, 10).until(
            EC.presence_of_element_located((By.ID, element_id))
        )
        field.send_keys(data)
        button = self.br.find_element(By.NAME, button_name)

        try:
            button.click()
        except TimeoutException:
            LOG.warning("page load timed out")

    def refresh(self):
        LOG.debug("reloading page")
        self.br.refresh()


def parseArgs() -> Args:
    p = argparse.ArgumentParser()

    p.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run Chrome in headless mode (default)",
    )
    p.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="Do not run Chrome in headless mode (show browser window)",
    )

    p.add_argument(
        "--extensions",
        action="store_true",
        default=True,
        help="Enable browser extensions",
    )
    p.add_argument(
        "--no-extensions",
        action="store_false",
        dest="extensions",
        help="Disable browser extensions",
    )

    p.add_argument(
        "--page-timeout", "-t", type=int, default=10, help="Set page timeout in seconds"
    )
    p.add_argument(
        "--check-interval",
        "-i",
        type=int,
        dest="interval",
        default=30,
        help="How often to check for delivery",
    )
    p.add_argument("--once", action="store_true", help="Check once and exit")
    p.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
    )

    p.add_argument(
        "--command", "-c", help="Run this command when your order has arrived"
    )

    args = Args(**vars(p.parse_args()))
    return args


def configureLogging(loglevel: str | int):
    formatter = logging.Formatter(
        fmt="%(asctime)s %(name)s %(levelname)-8s %(message)s",
        datefmt="%F %H:%M",
    )
    handler = logging.StreamHandler()
    handler.setLevel(loglevel)
    handler.setFormatter(formatter)
    LOG.setLevel(loglevel)
    LOG.addHandler(handler)


def main():
    args = parseArgs()
    loglevel = LOG_LEVELS[args.verbose]
    configureLogging(loglevel)

    # get credentials
    relish_username = keyring.get_password("relish-notifier", "EMAIL")
    relish_password = keyring.get_password("relish-notifier", "PASSWORD")
    if not (relish_username and relish_password):
        sys.exit("missing credentials")

    notifier = Notifier(
        Credentials(username=relish_username, password=relish_password),
        headless=args.headless,
        extensions=args.extensions,
        pageTimeout=args.page_timeout,
    )

    try:
        notifier.login()

        while True:
            status = notifier.checkOrderStatus()
            LOG.debug(f"notifier reports status: '{status}'")
            if status == OrderStatus.ARRIVED:
                print("order has arrived")
                if args.command is not None:
                    subprocess.run(args.command, shell=True)
                break
            if args.once:
                sys.exit("order has not arrived")
            LOG.info(f"Checking again in {args.interval} seconds...")
            sleep(args.interval)
            notifier.refresh()
    except KeyboardInterrupt:
        pass
    finally:
        notifier.close()

    sys.exit(0)


if __name__ == "__main__":
    main()
