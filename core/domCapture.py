from bs4 import BeautifulSoup


def capture_dom_state(driver, label="baseline"):
    print(f"[INFO] Capturing DOM ({label})...")

    dom_html = driver.execute_script("return document.documentElement.outerHTML;")
    soup = BeautifulSoup(dom_html, "lxml")

    css_data = {}
    elements = driver.find_elements("xpath", "//*")

    for el in elements:
        try:
            css_data[el.id] = driver.execute_script("""
                var s = window.getComputedStyle(arguments[0]);
                return {
                    color: s.color,
                    background: s.backgroundColor,
                    fontSize: s.fontSize,
                    display: s.display,
                    visibility: s.visibility,
                    opacity: s.opacity,
                    zIndex: s.zIndex
                };
            """, el)
        except:
            continue

    screenshot_path = None 
    # screenshot_path = f"assets/{label}_screenshot.png"
    # driver.save_screenshot(screenshot_path)

    return {
        "dom": soup,
        "css": css_data,
        "screenshot": screenshot_path
    }
