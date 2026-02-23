def detect_dark_patterns(dom_changes, css_changes, screenshot_change):
    new_dom, removed_dom = dom_changes
    patterns = []

    # Popup detection
    if any("modal" in el.lower() or "popup" in el.lower() for el in new_dom):
        patterns.append("⚠ Popup / Forced interaction detected")

    # CTA manipulation
    for _, old_css, new_css in css_changes:
        if old_css.get("background") != new_css.get("background"):
            patterns.append("⚠ CTA color manipulation detected")

    # Visual overlays
    # if screenshot_change[0]:
    #     patterns.append("⚠ Visual overlay or blocker detected")

    return patterns
