import json
import logging
import os
from datetime import datetime
from colorama import Fore, Style, init as colorama_init
from core.utils import ensure_asset_folders

colorama_init(autoreset=True)
logger = logging.getLogger(__name__)

REPORT_PATH = "assets/logs/report.json"


def generate_report(
    url: str,
    dom_changes: tuple[set, set],
    css_changes: list[tuple],
    screenshot_change: tuple[bool, tuple | None],
    patterns: list[str],
) -> dict:
    """
    Print a formatted console report and persist results to JSON.

    Returns:
        The report dict that was saved.
    """
    ensure_asset_folders()
    new_dom, removed_dom = dom_changes
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # ── Console output ────────────────────────────────────────────────────────
    print(f"\n{Fore.YELLOW}{'=' * 50}")
    print(f"{Fore.YELLOW}  ETHIX — DARK PATTERN REPORT")
    print(f"{Fore.YELLOW}{'=' * 50}{Style.RESET_ALL}")
    print(f"  URL       : {url}")
    print(f"  Timestamp : {timestamp}")

    print(f"\n{Fore.CYAN}[DOM CHANGES]{Style.RESET_ALL}")
    print(f"  + New elements     : {len(new_dom)}")
    print(f"  - Removed elements : {len(removed_dom)}")

    print(f"\n{Fore.CYAN}[CSS CHANGES]{Style.RESET_ALL}")
    if css_changes:
        for elem_id, old_css, new_css in css_changes[:10]:
            changed_props = {k: (old_css.get(k), new_css.get(k))
                             for k in new_css if old_css.get(k) != new_css.get(k)}
            print(f"  * Element {str(elem_id)[:12]}: {changed_props}")
        if len(css_changes) > 10:
            print(f"  … and {len(css_changes) - 10} more CSS changes (see report.json)")
    else:
        print("  No CSS changes detected.")

    print(f"\n{Fore.CYAN}[SCREENSHOT ANALYSIS]{Style.RESET_ALL}")
    if screenshot_change[0]:
        print(f"  {Fore.RED}⚠ Visual change detected in region: {screenshot_change[1]}{Style.RESET_ALL}")
    else:
        print("  No significant visual changes detected.")

    print(f"\n{Fore.CYAN}[POTENTIAL DARK PATTERNS]{Style.RESET_ALL}")
    if patterns:
        for p in patterns:
            print(f"  {Fore.RED}{p}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.GREEN}✔ No dark pattern signals detected.{Style.RESET_ALL}")

    # ── Persist JSON report ───────────────────────────────────────────────────
    report = {
        "url":               url,
        "timestamp":         timestamp,
        "dom_changes": {
            "new_elements":     list(new_dom),
            "removed_elements": list(removed_dom),
        },
        "css_changes": [
            {"element_id": eid, "old": old, "new": new}
            for eid, old, new in css_changes
        ],
        "screenshot_change": {
            "detected": screenshot_change[0],
            "region":   screenshot_change[1],
        },
        "patterns":          patterns,
        "severity":          _severity(patterns),
    }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print(f"\n{Fore.GREEN}Report saved → {REPORT_PATH}{Style.RESET_ALL}\n")
    logger.info("Report saved to %s", REPORT_PATH)
    return report


def _severity(patterns: list[str]) -> str:
    """Simple severity rating based on pattern count."""
    n = len(patterns)
    if n == 0:
        return "CLEAN"
    if n <= 2:
        return "LOW"
    if n <= 5:
        return "MEDIUM"
    return "HIGH"
