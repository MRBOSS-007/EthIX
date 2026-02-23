import time
import random
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    StaleElementReferenceException,
    MoveTargetOutOfBoundsException,
)

logger = logging.getLogger(__name__)

# ── tuneable constants ────────────────────────────────────────────────────────
SCROLL_STEPS        = 8          # number of scroll increments
SCROLL_STEP_PX      = 300        # pixels per scroll step
SCROLL_DELAY        = (0.25, 0.6)
HOVER_DELAY         = (0.15, 0.4)
CLICK_DELAY         = (0.3, 0.7)
MAX_CLICKABLE       = 20
MAX_INPUT_FIELDS    = 5
FAKE_INPUT_SAMPLES  = ["test@example.com", "John Doe", "12345"]


def _random_delay(bounds: tuple[float, float]) -> None:
    time.sleep(random.uniform(*bounds))


def human_interaction(driver: WebDriver) -> None:
    """
    Simulate realistic human browsing behavior:
      1. Gradual scroll to the bottom and back.
      2. Hover over and click interactive elements.
      3. Fill visible input fields with benign sample data.
    """
    logger.info("Simulating human-like interaction…")
    actions = ActionChains(driver)

    # ── 1. Scroll down gradually ─────────────────────────────────────────────
    for _ in range(SCROLL_STEPS):
        driver.execute_script(f"window.scrollBy(0, {SCROLL_STEP_PX});")
        _random_delay(SCROLL_DELAY)

    # ── 2. Hover + conditional click on interactive elements ─────────────────
    clickable_xpath = (
        "//*[self::button or self::a"
        " or @onclick or @role='button'"
        " or @role='link' or @tabindex]"
    )
    buttons = driver.find_elements(By.XPATH, clickable_xpath)
    logger.info("Found %d interactive elements; processing up to %d.", len(buttons), MAX_CLICKABLE)

    for btn in buttons[:MAX_CLICKABLE]:
        try:
            if not btn.is_displayed():
                continue

            actions.move_to_element(btn).perform()
            _random_delay(HOVER_DELAY)

            tag = btn.tag_name.lower()
            role = (btn.get_attribute("role") or "").lower()

            if tag in ("button", "a") or role in ("button", "link"):
                btn.click()
                _random_delay(CLICK_DELAY)
                logger.debug("Clicked element: <%s> role=%s", tag, role)

        except (ElementNotInteractableException, StaleElementReferenceException,
                MoveTargetOutOfBoundsException):
            continue
        except Exception as e:
            logger.debug("Skipping element due to: %s", e)
            continue

    # ── 3. Fill visible text inputs ──────────────────────────────────────────
    fields = driver.find_elements(By.XPATH,
        "//input[@type='text' or @type='email' or @type='search' or not(@type)]"
        " | //textarea"
    )
    logger.info("Found %d input fields; filling up to %d.", len(fields), MAX_INPUT_FIELDS)

    for field in fields[:MAX_INPUT_FIELDS]:
        try:
            if not field.is_displayed() or not field.is_enabled():
                continue
            field.clear()
            field.send_keys(random.choice(FAKE_INPUT_SAMPLES))
            _random_delay((0.1, 0.3))
        except Exception as e:
            logger.debug("Skipping input field: %s", e)
            continue

    # ── 4. Scroll back to top ────────────────────────────────────────────────
    driver.execute_script("window.scrollTo(0, 0);")
    logger.info("Human interaction simulation complete.")
