from core.driver import init_driver
from core.domCapture import capture_dom_state
from core.humanActions import human_interaction
from core.diff_Engine import compare_dom, compare_css, compare_screenshots
from core.pattern import detect_dark_patterns
from core.report import generate_report
from core.utils import ensure_asset_folders
import time


def main():
    ensure_asset_folders() 
    url = input("Enter URL to analyze: ")

    driver = init_driver()
    driver.get(url)
    time.sleep(3)

    # 1) Capture baseline
    baseline = capture_dom_state(driver, label="baseline")

    # 2) Human simulation
    human_interaction(driver)

    # 3) Capture post interaction
    post = capture_dom_state(driver, label="post")

    # 4) Calculate differences
    dom_diff = compare_dom(baseline["dom"], post["dom"])
    css_diff = compare_css(baseline["css"], post["css"])
    screenshot_diff = compare_screenshots(baseline["screenshot"], post["screenshot"])

    # 5) Pattern detection
    patterns = detect_dark_patterns(dom_diff, css_diff, screenshot_diff)

    # 6) Report output
    generate_report(url, dom_diff, css_diff, screenshot_diff, patterns)

    driver.quit()


if __name__ == "__main__":
    main()
