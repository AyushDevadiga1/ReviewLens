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
    Short terms and API misses yield [] — an empty dropdown, not an error.
    """
    term = term.strip()
    if len(term) < 2:
        return []
    try:
        results = cached_get("/products/search", (("query", term),))
    except RuntimeError:
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
