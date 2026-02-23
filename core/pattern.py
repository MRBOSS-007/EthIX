import logging
import re

logger = logging.getLogger(__name__)

# ── keyword sets ─────────────────────────────────────────────────────────────
POPUP_KEYWORDS     = {"modal", "popup", "overlay", "dialog", "lightbox", "interstitial"}
URGENCY_KEYWORDS   = {"countdown", "timer", "limited", "hurry", "expire", "last chance",
                      "only left", "selling fast"}
CONSENT_KEYWORDS   = {"cookie", "gdpr", "consent", "accept all", "agree", "privacy notice"}
SUBSCRIPTION_KEYS  = {"subscribe", "sign up", "trial", "free trial", "cancel anytime",
                      "recurring", "auto-renew"}

# CSS properties whose changes are considered suspicious
SUSPICIOUS_BG_CHANGE    = True   # CTA background color shift
OPACITY_THRESHOLD       = 0.3    # opacity below this is "hidden"
HIGH_ZINDEX_THRESHOLD   = 100    # z-index above this may be an overlay


def _tag_text(fp: str) -> str:
    """Extract the text segment from a DOM fingerprint string."""
    parts = fp.split("|")
    return parts[-1].lower() if len(parts) >= 3 else fp.lower()


def _matches_any(text: str, keyword_set: set) -> bool:
    return any(kw in text for kw in keyword_set)


def detect_dark_patterns(
    dom_changes: tuple[set, set],
    css_changes: list[tuple],
    screenshot_change: tuple[bool, tuple | None],
) -> list[str]:
    """
    Rule-based dark pattern detector.

    Args:
        dom_changes:       (new_elements, removed_elements) from compare_dom.
        css_changes:       list of (elem_id, old_css, new_css) from compare_css.
        screenshot_change: (changed: bool, bbox) from compare_screenshots.

    Returns:
        List of human-readable pattern warning strings.
    """
    new_dom, removed_dom = dom_changes
    patterns: list[str] = []
    seen: set[str] = set()          # deduplicate

    def add(msg: str) -> None:
        if msg not in seen:
            seen.add(msg)
            patterns.append(msg)
            logger.info("Pattern detected: %s", msg)

    # ── DOM-based detections ──────────────────────────────────────────────────

    for fp in new_dom:
        text = _tag_text(fp)
        combined = fp.lower()

        if _matches_any(combined, POPUP_KEYWORDS):
            add("⚠ Popup / Forced interaction detected (new DOM element)")

        if _matches_any(text, URGENCY_KEYWORDS):
            add("⚠ Urgency / scarcity manipulation detected (countdown or limited-offer language)")

        if _matches_any(text, CONSENT_KEYWORDS):
            add("⚠ Cookie consent or GDPR dark pattern detected (post-interaction injection)")

        if _matches_any(text, SUBSCRIPTION_KEYS):
            add("⚠ Hidden subscription or auto-renewal element detected")

    # Nagging / roach motel: subscribe added but unsubscribe not present
    new_text_all = " ".join(_tag_text(fp) for fp in new_dom)
    if "subscribe" in new_text_all and "unsubscribe" not in new_text_all:
        add("⚠ Roach motel pattern: subscribe option added without unsubscribe equivalent")

    # ── CSS-based detections ──────────────────────────────────────────────────

    for _, old_css, new_css in css_changes:
        # CTA color manipulation
        if SUSPICIOUS_BG_CHANGE and old_css.get("background") != new_css.get("background"):
            add("⚠ CTA color manipulation detected (background changed post-interaction)")

        # Visibility manipulation
        old_vis = old_css.get("visibility", "visible")
        new_vis = new_css.get("visibility", "visible")
        if old_vis == "hidden" and new_vis == "visible":
            add("⚠ Hidden element revealed after interaction (visibility: hidden → visible)")

        # Opacity manipulation
        try:
            new_op = float(new_css.get("opacity", 1))
            old_op = float(old_css.get("opacity", 1))
            if old_op >= 1.0 and new_op <= OPACITY_THRESHOLD:
                add("⚠ Deceptive opacity manipulation (element faded out post-interaction)")
        except (TypeError, ValueError):
            pass

        # z-index elevation (overlay injection)
        try:
            old_z = int(old_css.get("zIndex", 0) or 0)
            new_z = int(new_css.get("zIndex", 0) or 0)
            if new_z > HIGH_ZINDEX_THRESHOLD and old_z <= HIGH_ZINDEX_THRESHOLD:
                add("⚠ Overlay / z-index elevation detected (possible blocking layer)")
        except (TypeError, ValueError):
            pass

        # Display toggling
        if old_css.get("display") == "none" and new_css.get("display") != "none":
            add("⚠ Hidden element shown after interaction (display: none removed)")

    # ── Screenshot-based detections ───────────────────────────────────────────

    if screenshot_change[0]:
        bbox = screenshot_change[1]
        add(f"⚠ Visual overlay or layout change detected in region {bbox}")

    return patterns
