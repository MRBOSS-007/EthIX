import json
from colorama import Fore
import os
from core.utils import ensure_asset_folders



def generate_report(url, dom_changes, css_changes, screenshot_change, patterns):
    ensure_asset_folders() 
    print(f"\n{Fore.YELLOW}=== DARK PATTERN REPORT ===")
    print(f"URL: {url}")

    new_dom, removed_dom = dom_changes

    print("\n[DOM CHANGES]")
    print(f"+ New elements: {len(new_dom)}")
    print(f"- Removed elements: {len(removed_dom)}")

    print("\n[CSS CHANGES]")
    for ch in css_changes[:10]:
        print("* CSS changed:", ch)

    print("\n[SCREENSHOT]")
    if screenshot_change[0]:
        print(f"* Overlay detected at: {screenshot_change[1]}")
    else:
        print("* No screenshot anomalies")

    print("\n[POTENTIAL DARK PATTERNS]")
    if patterns:
        for p in patterns:
            print(p)
    else:
        print("No strong dark pattern signals detected")

    # Save log
    with open("assets/logs/report.json", "w") as f:
        json.dump({
            "new_dom": list(new_dom),
            "removed_dom": list(removed_dom),
            "css_changes": css_changes,
            "screenshot_change": screenshot_change,
            "patterns": patterns
        }, f, indent=4)

    print(f"\n{Fore.GREEN}Report saved at assets/logs/report.json\n")
