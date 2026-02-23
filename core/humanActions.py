import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


def human_interaction(driver):
    print("[INFO] Simulating human-like activity...")

    actions = ActionChains(driver)

    # Scroll slowly
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(random.uniform(0.3, 0.7))

    # Hover and click clickable elements
    buttons = driver.find_elements(By.XPATH, "//*[@onclick or @href or self::button]")

    for btn in buttons[:15]:  # limit to avoid runaway clicking
        try:
            actions.move_to_element(btn).perform()
            time.sleep(0.2)

            if btn.tag_name.lower() in ["button", "a"]:
                btn.click()
                time.sleep(0.5)

        except:
            continue

    # Input text fields
    fields = driver.find_elements(By.TAG_NAME, "input")
    for field in fields[:3]:
        try:
            field.send_keys("test input")
            time.sleep(0.2)
        except:
            continue

    driver.execute_script("window.scrollTo(0, 0);")
