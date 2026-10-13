"""api_client.py
Shared HTTP layer for the Streamlit pages: base URL, auth header, timeouts.
Single place to change when the API moves.

Env:
  API_BASE_URL  — e.g. http://localhost:8000 locally, http://api:8000 in compose
  API_KEY       — value of the X-API-Key header (falls back to API_KEY_SECRET
                  so a local .env works without extra configuration)
"""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # local `streamlit run` picks up .env; compose injects env directly

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
ENV_API_KEY = os.getenv("API_KEY", os.getenv("API_KEY_SECRET", ""))

ANALYZE_TIMEOUT = 1500  # Band-aid: a 171-review product needs ~20 min CPU.
# Proper cure is async jobs (submit → poll), tracked as a project stage.
DEFAULT_TIMEOUT = 60

try:
    from ml.absa.aspects import ASPECTS
except ImportError:  # import path differs between local runs and the image
    ASPECTS = {
        "battery": {"display_name": "Battery Life"},
        "camera": {"display_name": "Camera"},
        "display": {"display_name": "Display"},
        "build_quality": {"display_name": "Build Quality"},
        "value": {"display_name": "Value for Money"},
        "delivery": {"display_name": "Delivery"},
        "performance": {"display_name": "Performance"},
    }


def effective_api_key() -> str:
    """Sidebar override wins (demo convenience), env is the default."""
    try:
        override = st.session_state.get("api_key_override", "")
    except Exception:
        override = ""
    return (override or ENV_API_KEY).strip()


def _headers() -> dict:
    key = effective_api_key()
    return {"X-API-Key": key} if key else {}


def _checked(response: requests.Response) -> dict:
    """Return parsed JSON, or raise with the server's own error detail."""
    if response.status_code == 429:
        raise RuntimeError(
            "API 429: rate limited (100 req/min) — wait a few seconds "
            "and press the button again, don't spam-click.")
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"API {response.status_code}: {detail}")
    return response.json()


def api_get(path: str, params: dict = None) -> dict:
    response = requests.get(
        API_BASE + path, params=params, headers=_headers(),
        timeout=DEFAULT_TIMEOUT,
    )
    return _checked(response)


def api_post(path: str, payload: dict) -> dict:
    response = requests.post(
        API_BASE + path, json=payload, headers=_headers(),
        timeout=ANALYZE_TIMEOUT,
    )
    return _checked(response)


def api_delete(path: str) -> dict:
    response = requests.delete(
        API_BASE + path, headers=_headers(), timeout=DEFAULT_TIMEOUT,
    )
    return _checked(response)


@st.cache_data(ttl=300)
def cached_get(path: str, params_key: tuple = ()) -> dict:
    """Cached GET for navigation that must not re-hit the API.

    Params travel as a tuple of pairs (hashable for the cache);
    POST /analyze stays uncached on purpose — every run is new work.
    """
    params = dict(params_key) or None
    response = requests.get(
        API_BASE + path, params=params, headers=_headers(),
        timeout=DEFAULT_TIMEOUT,
    )
    return _checked(response)


@st.cache_data(ttl=30)
def api_health() -> dict:
    """Fresh-enough backend status for the sidebar indicator."""
    return api_get("/health/")


def product_search_options(term: str, stash_key: str) -> list:
    """Suggestion list for st_searchbox, backed by GET /products/search.

    Returns display labels; stashes the label→product mapping in
    session state under stash_key (one key per searchbox instance).
    Short terms and empty results yield [] — an empty dropdown, not an
    error. Auth failures are the exception: a wrong key would otherwise
    look exactly like "no products", so they surface loudly instead.
    """
    term = term.strip()
    if len(term) < 2:
        return []
    try:
        results = cached_get("/products/search", (("query", term),))
    except RuntimeError as exc:
        if "401" in str(exc):
            st.error("API key rejected — set API_KEY to match the "
                     "server's API_KEY_SECRET, then rerun.")
        return []
    opts = {
        f"{p['product_name']} ({p['platform']}, "
        f"{p['review_count']} reviews)": p
        for p in results
    }
    st.session_state[stash_key] = opts
    return list(opts)


def take_product_match(label: str, stash_key: str):
    """Resolve a picked suggestion label back to its product dict."""
    if not label:
        return None
    return st.session_state.get(stash_key, {}).get(label)


FRIENDLY_PRODUCT_NAMES = {
    "7508492919": "Rhinestone Bling Protective Phone Case",
    "7887421268": "Ultra-Slim Flexible TPU Phone Case",
    "8288853439": "Rapid Wall Charger & Sync Cable",
    "961301375X": "Heavy-Duty Fast Charging Long Cord",
    "8288878881": "10000mAh Ultra-Slim Portable Power Bank",
    "9707716371": "True Wireless Noise-Cancelling Earbuds",
    "8288862993": "9H Hardness Tempered Glass (3-Pack)",
    "7532385086": "Shockproof Rugged Dual-Layer Armor Case",
    "9658231969": "30W Dual-Port USB-C Fast Wall Adapter",
    "9707716436": "Sweatproof Sports Bluetooth Earphones",
    "9678315173": "Water-Resistant Running Fitness Armband",
    "828886922X": "Matte Privacy Screen Filter Shield",
    "9578085451": "Dual-Layer Kickstand Armor Protective Case",
    "9713957334": "3-in-1 Retractable Multi Charging Cable",
    "8199900164": "360-Degree Magnetic Ring Grip Holder",
    "9652676748": "Deep Bass In-Ear Stereo Headset with Mic",
    "9638762632": "Qi Wireless Fast Charging Desktop Stand",
}


def get_friendly_name(raw_name: str) -> str:
    """Translate raw ASIN codes into meaningful consumer product titles."""
    raw = str(raw_name).strip()
    return FRIENDLY_PRODUCT_NAMES.get(raw, f"Product {raw}")


def format_product_label(p: dict) -> str:
    """Human-readable product label for selectboxes and multiselects."""
    raw_name = str(p.get("product_name", "")).strip()
    friendly = get_friendly_name(raw_name)
    tag = "Analyzed" if p.get("aspect_count", 0) > 0 else "Not analyzed"
    plat = p.get("platform", "amazon").upper()
    revs = p.get("review_count", 0)
    return f"[{plat}] {friendly} (ASIN: {raw_name} · {revs} reviews) · [{tag}]"
