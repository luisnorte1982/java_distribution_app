"""
OData V4 client for Business Central with OAuth2 authentication.
Handles pagination, retries, and token caching.
"""
import time
import requests
import streamlit as st
from msal import ConfidentialClientApplication
from config.settings import (
    BC_TENANT_ID, BC_CLIENT_ID, BC_CLIENT_SECRET, BC_SCOPE, ENDPOINTS,
)


def get_access_token(tenant_id: str, client_id: str, client_secret: str, scope: str) -> str:
    """Acquire an OAuth2 access token via client_credentials flow."""
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = ConfidentialClientApplication(
        client_id, authority=authority, client_credential=client_secret,
    )
    result = app.acquire_token_for_client(scopes=[scope])
    if "access_token" in result:
        return result["access_token"]
    raise RuntimeError(f"Token acquisition failed: {result.get('error_description', result)}")


@st.cache_data(ttl=3600, show_spinner="Authentification Business Central…")
def cached_access_token() -> str:
    """Return a cached access token (refreshed every hour)."""
    return get_access_token(BC_TENANT_ID, BC_CLIENT_ID, BC_CLIENT_SECRET, BC_SCOPE)


def fetch_odata(endpoint_key: str, token: str | None = None, max_retries: int = 3) -> list[dict]:
    """
    Fetch all pages from an OData V4 endpoint.
    Returns a list of dicts (rows).
    """
    if token is None:
        token = cached_access_token()

    url = ENDPOINTS[endpoint_key]
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    }
    all_records: list[dict] = []
    page = 0

    while url:
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, headers=headers, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                records = data.get("value", [])
                all_records.extend(records)
                url = data.get("@odata.nextLink")
                page += 1
                break
            except requests.exceptions.RequestException as exc:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise RuntimeError(
                        f"OData fetch failed for {endpoint_key} after {max_retries} attempts: {exc}"
                    ) from exc

    return all_records


def fetch_all_endpoints(token: str | None = None, progress_callback=None) -> dict[str, list[dict]]:
    """Fetch all 12 endpoints and return a dict of raw data."""
    if token is None:
        token = cached_access_token()
    
    results = {}
    endpoint_keys = list(ENDPOINTS.keys())
    for i, key in enumerate(endpoint_keys):
        if progress_callback:
            progress_callback(i / len(endpoint_keys), f"Chargement: {key}…")
        results[key] = fetch_odata(key, token)
    
    if progress_callback:
        progress_callback(1.0, "Données chargées ✓")
    
    return results
