from PIL import Image, ImageChops


def compare_dom(dom_before, dom_after):
    new = set(map(str, dom_after.find_all())) - set(map(str, dom_before.find_all()))
    removed = set(map(str, dom_before.find_all())) - set(map(str, dom_after.find_all()))
    return new, removed


def compare_css(css_before, css_after):
    changes = []
    for key in css_after:
        if key in css_before and css_before[key] != css_after[key]:
            changes.append((key, css_before[key], css_after[key]))
    return changes


def compare_screenshots(before_path, after_path):
    # img1 = Image.open(before_path)
    # img2 = Image.open(after_path)

    # diff = ImageChops.difference(img1, img2)

    # bbox = diff.getbbox()
    # if bbox:
    #     return True, bbox
    return False, None
