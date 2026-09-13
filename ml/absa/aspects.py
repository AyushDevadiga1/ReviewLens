"""
aspects.py
Aspect category definitions for ReviewLens.
These are the dimensions measured per product.
Add or remove aspects here — changes propagate everywhere.
"""

# Core aspects for electronics / smartphones
# Each aspect has: canonical name, display name, keywords
# Keywords help with aspect matching if needed

ASPECTS = {
    "battery": {
        "display_name": "Battery Life",
        "keywords": ["battery", "charge", "charging", "mah", "drain", "life"],
        "icon": "🔋"
    },
    "camera": {
        "display_name": "Camera",
        "keywords": ["camera", "photo", "picture", "selfie", "lens", "megapixel"],
        "icon": "📷"
    },
    "display": {
        "display_name": "Display",
        "keywords": ["screen", "display", "amoled", "lcd", "brightness", "resolution"],
        "icon": "🖥️"
    },
    "build_quality": {
        "display_name": "Build Quality",
        "keywords": ["build", "quality", "plastic", "glass", "metal", "premium", "solid"],
        "icon": "🏗️"
    },
    "value": {
        "display_name": "Value for Money",
        "keywords": ["price", "value", "worth", "expensive", "cheap", "budget", "money"],
        "icon": "💰"
    },
    "delivery": {
        "display_name": "Delivery",
        "keywords": ["delivery", "shipping", "courier", "arrived", "packaging", "days"],
        "icon": "📦"
    },
    "performance": {
        "display_name": "Performance",
        "keywords": ["fast", "slow", "lag", "performance", "processor", "smooth", "speed"],
        "icon": "⚡"
    },
}

ASPECT_NAMES = list(ASPECTS.keys())
ASPECT_DISPLAY_NAMES = {k: v["display_name"] for k, v in ASPECTS.items()}