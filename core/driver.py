from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import logging

logger = logging.getLogger(__name__)


def init_driver(headless: bool = True, window_size: tuple = (1920, 1080)) -> webdriver.Chrome:
    """
    Initialize and return a configured Chrome WebDriver instance.

    Args:
        headless: Run browser in headless mode (default True).
        window_size: Browser window dimensions as (width, height).

    Returns:
        Configured Chrome WebDriver.
    """
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")          # prevent /dev/shm OOM in Docker
    options.add_argument("--disable-gpu")                    # required in some headless envs
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")  # reduce bot detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)

    logger.info("Chrome WebDriver initialized (headless=%s, size=%sx%s)", headless, *window_size)
    return driver
