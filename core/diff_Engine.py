import logging
from PIL import Image, ImageChops, ImageFilter
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def compare_dom(dom_before: BeautifulSoup, dom_after: BeautifulSoup) -> tuple[set, set]:
    """
    Return (new_elements, removed_elements) as sets of stringified HTML tags.
    Uses tag + attribute fingerprints for more accurate diffing.
    """
    def _fingerprint(tag) -> str:
        return f"{tag.name}|{sorted(tag.attrs.items()) if tag.attrs else ''}|{(tag.string or '').strip()[:80]}"

    before_set = {_fingerprint(t) for t in dom_before.find_all()}
    after_set  = {_fingerprint(t) for t in dom_after.find_all()}

    new_elements     = after_set  - before_set
    removed_elements = before_set - after_set

    logger.info("DOM diff — new: %d, removed: %d", len(new_elements), len(removed_elements))
    return new_elements, removed_elements


def compare_css(css_before: dict, css_after: dict) -> list[tuple]:
    """
    Return list of (element_id, old_css, new_css) for elements whose CSS changed.
    Only elements present in both snapshots are compared.
    """
    changes = []
    common_keys = css_before.keys() & css_after.keys()

    for key in common_keys:
        old, new = css_before[key], css_after[key]
        if old != new:
            changes.append((key, old, new))

    logger.info("CSS diff — %d changes detected.", len(changes))
    return changes


def compare_screenshots(before_path: str | None, after_path: str | None) -> tuple[bool, tuple | None]:
    """
    Pixel-level diff between two screenshots.

    Returns:
        (changed: bool, bounding_box: tuple | None)
        bounding_box is (left, upper, right, lower) of the changed region, or None.
    """
    if not before_path or not after_path:
        logger.warning("Screenshot path(s) missing — skipping visual diff.")
        return False, None

    try:
        img1 = Image.open(before_path).convert("RGB")
        img2 = Image.open(after_path).convert("RGB")

        # Ensure same size (crop to smaller if pages differ in height after interaction)
        min_height = min(img1.height, img2.height)
        img1 = img1.crop((0, 0, img1.width, min_height))
        img2 = img2.crop((0, 0, img2.width, min_height))

        diff = ImageChops.difference(img1, img2)

        # Apply a slight blur to ignore anti-aliasing noise
        diff_blurred = diff.filter(ImageFilter.GaussianBlur(radius=1))

        bbox = diff_blurred.getbbox()
        if bbox:
            logger.info("Visual change detected in region: %s", bbox)
            return True, bbox

        logger.info("No significant visual changes detected.")
        return False, None

    except FileNotFoundError as e:
        logger.error("Screenshot file not found: %s", e)
        return False, None
    except Exception as e:
        logger.error("Screenshot comparison failed: %s", e)
        return False, None
