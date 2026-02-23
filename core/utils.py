import os
import logging

logger = logging.getLogger(__name__)

ASSET_DIRS = [
    "assets",
    "assets/logs",
    "assets/dom",
    "assets/css",
    "assets/diffs",
    "assets/screenshots",
]


def ensure_asset_folders() -> None:
    """Create all required asset directories if they don't already exist."""
    for directory in ASSET_DIRS:
        os.makedirs(directory, exist_ok=True)
    logger.debug("Asset folders verified: %s", ASSET_DIRS)
