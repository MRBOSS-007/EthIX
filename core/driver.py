from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def init_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    return driver
