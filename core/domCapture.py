import os
import logging
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = "assets/screenshots"
CSS_PROPERTIES = (
    "color", "backgroundColor", "fontSize", "display",
    "visibility", "opacity", "zIndex", "width", "height",
    "position", "overflow", "transform", "pointerEvents",
)

_CSS_SCRIPT = """
var s = window.getComputedStyle(arguments[0]);
return {
    color:           s.color,
    background:      s.backgroundColor,
    fontSize:        s.fontSize,
    display:         s.display,
    visibility:      s.visibility,
    opacity:         s.opacity,
    zIndex:          s.zIndex,
    width:           s.width,
    height:          s.height,
    position:        s.position,
    overflow:        s.overflow,
    transform:       s.transform,
    pointerEvents:   s.pointerEvents
};
"""


def _capture_screenshot(driver: WebDriver, label: str) -> str | None:
    """
    Save a full-page screenshot and return the file path.
    Falls back to a viewport screenshot if the CDP full-page method is unavailable.
    """
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    path = os.path.join(SCREENSHOT_DIR, f"{label}_screenshot.png")

    try:
        # Attempt full-page screenshot via Chrome DevTools Protocol
        metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
        width  = metrics["contentSize"]["width"]
        height = metrics["contentSize"]["height"]

        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "mobile":             False,
            "width":              width,
            "height":             height,
            "deviceScaleFactor":  1,
        })

        screenshot_data = driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {"format": "png", "fromSurface": True, "captureBeyondViewport": True},
        )

        import base64
        with open(path, "wb") as f:
            f.write(base64.b64decode(screenshot_data["data"]))

        # Restore original viewport
        driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
        logger.info("Full-page screenshot saved: %s", path)

    except Exception as cdp_err:
        logger.warning("CDP full-page screenshot failed (%s); falling back to viewport.", cdp_err)
        try:
            driver.save_screenshot(path)
            logger.info("Viewport screenshot saved: %s", path)
        except Exception as vp_err:
            logger.error("Screenshot capture failed entirely: %s", vp_err)
            return None

    return path


def capture_dom_state(driver: WebDriver, label: str = "baseline") -> dict:
    """
    Capture a snapshot of the current page state including DOM, CSS, and screenshot.

    Args:
        driver: Active Selenium WebDriver.
        label:  Human-readable label for the snapshot (e.g. 'baseline', 'post_interaction').

    Returns:
        dict with keys: 'dom' (BeautifulSoup), 'css' (dict), 'screenshot' (str | None).
    """
    logger.info("Capturing DOM state (%s)…", label)

    # ── DOM ──────────────────────────────────────────────────────────────────
    dom_html = driver.execute_script("return document.documentElement.outerHTML;")
    soup = BeautifulSoup(dom_html, "lxml")

    # ── CSS ──────────────────────────────────────────────────────────────────
    css_data: dict[str, dict] = {}
    elements = driver.find_elements("xpath", "//*")

    for el in elements:
        try:
            css_data[el.id] = driver.execute_script(_CSS_SCRIPT, el)
        except Exception:
            continue  # stale element or other transient issue

    logger.info("Captured CSS for %d elements.", len(css_data))

    # ── Screenshot ───────────────────────────────────────────────────────────
    screenshot_path = _capture_screenshot(driver, label)

    return {
        "dom":        soup,
        "css":        css_data,
        "screenshot": screenshot_path,
    }
