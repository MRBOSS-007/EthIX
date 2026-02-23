"""
Ethix — Dynamic Dark Pattern Detection System
Entry point: orchestrates browser automation, DOM capture, diffing, and reporting.

Usage:
    python main.py --url https://example.com
    python main.py --url https://example.com --no-headless
"""

import argparse
import logging
import sys

from core.driver import init_driver
from core.domCapture import capture_dom_state
from core.humanActions import human_interaction
from core.diff_Engine import compare_dom, compare_css, compare_screenshots
from core.pattern import detect_dark_patterns
from core.report import generate_report
from core.utils import ensure_asset_folders

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ethix")


def run(url: str, headless: bool = True) -> dict:
    ensure_asset_folders()
    driver = init_driver(headless=headless)

    try:
        logger.info("Loading URL: %s", url)
        driver.get(url)

        # ── Baseline snapshot ─────────────────────────────────────────────────
        baseline = capture_dom_state(driver, label="baseline")

        # ── Simulate human interaction ────────────────────────────────────────
        human_interaction(driver)

        # ── Post-interaction snapshot ─────────────────────────────────────────
        post = capture_dom_state(driver, label="post_interaction")

        # ── Diff analysis ─────────────────────────────────────────────────────
        dom_changes        = compare_dom(baseline["dom"], post["dom"])
        css_changes        = compare_css(baseline["css"], post["css"])
        screenshot_change  = compare_screenshots(baseline["screenshot"], post["screenshot"])

        # ── Pattern detection ─────────────────────────────────────────────────
        patterns = detect_dark_patterns(dom_changes, css_changes, screenshot_change)

        # ── Report ────────────────────────────────────────────────────────────
        report = generate_report(url, dom_changes, css_changes, screenshot_change, patterns)
        return report

    finally:
        driver.quit()
        logger.info("WebDriver closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ethix — Dark Pattern Detector")
    parser.add_argument("--url", required=True, help="Target URL to analyse")
    parser.add_argument("--no-headless", action="store_true",
                        help="Run browser with visible window (for debugging)")
    args = parser.parse_args()

    result = run(url=args.url, headless=not args.no_headless)
    sys.exit(0 if result["severity"] in ("CLEAN", "LOW") else 1)
