"""
OData V4 client for Business Central with OAuth2 authentication.
Handles pagination, retries, and token caching.
Supports DEBUG_MODE for detailed connection diagnostics.
"""
import logging
import time
import requests
import streamlit as st
from msal import ConfidentialClientApplication
from config.settings import (
    BC_TENANT_ID, BC_CLIENT_ID, BC_CLIENT_SECRET, BC_SCOPE, ENDPOINTS,
    DEBUG_MODE,
)

logger = logging.getLogger(__name__)

if DEBUG_MODE:
    logging.basicConfig(level=logging.DEBUG, format="[DEBUG-BC] %(message)s")


def _debug(msg: str):
    """Log debug info and show in Streamlit sidebar when DEBUG_MODE is on."""
    if DEBUG_MODE:
        logger.debug(msg)


def _safe_headers_log(headers: dict) -> dict:
    """Return a copy of headers with secrets masked."""
    safe = {}
    for k, v in headers.items():
        if k.lower() == "authorization" and v:
            safe[k] = f"Bearer {v[7:27]}..." if len(v) > 27 else "Bearer ***"
        else:
            safe[k] = v
    return safe


def get_access_token(tenant_id: str, client_id: str, client_secret: str, scope: str) -> str:
    """Acquire an OAuth2 access token via client_credentials flow."""
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    _debug(f"Authority : {authority}")
    _debug(f"Client ID : {client_id}")
    _debug(f"Scope     : {scope}")

    app = ConfidentialClientApplication(
        client_id, authority=authority, client_credential=client_secret,
    )
    result = app.acquire_token_for_client(scopes=[scope])

    if "access_token" in result:
        _debug(f"Token obtenu (longueur={len(result['access_token'])})")
        return result["access_token"]

    error_desc = result.get("error_description", str(result))
    _debug(f"Token ERREUR : {error_desc}")
    raise RuntimeError(f"Token acquisition failed: {error_desc}")


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

    _debug(f"[{endpoint_key}] URL initiale : {url}")
    _debug(f"[{endpoint_key}] Headers : {_safe_headers_log(headers)}")

    while url:
        for attempt in range(max_retries):
            try:
                _debug(f"[{endpoint_key}] Requête page {page} (tentative {attempt+1}/{max_retries})")
                resp = requests.get(url, headers=headers, timeout=120)

                _debug(f"[{endpoint_key}] HTTP {resp.status_code}")
                if DEBUG_MODE and resp.status_code != 200:
                    _debug(f"[{endpoint_key}] Response headers : {dict(resp.headers)}")
                    _debug(f"[{endpoint_key}] Response body (extrait) : {resp.text[:500]}")

                resp.raise_for_status()
                data = resp.json()
                records = data.get("value", [])
                all_records.extend(records)
                url = data.get("@odata.nextLink")
                page += 1
                _debug(f"[{endpoint_key}] Page {page} : {len(records)} enregistrements")
                break
            except requests.exceptions.RequestException as exc:
                _debug(f"[{endpoint_key}] ERREUR tentative {attempt+1} : {exc}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    error_msg = (
                        f"OData fetch failed for {endpoint_key} after {max_retries} attempts: "
                        f"{resp.status_code if 'resp' in dir() else 'N/A'} {exc}"
                    )
                    raise RuntimeError(error_msg) from exc

    _debug(f"[{endpoint_key}] Total : {len(all_records)} enregistrements")
    return all_records


def fetch_all_endpoints(token: str | None = None, progress_callback=None) -> dict[str, list[dict]]:
    """Fetch all endpoints and return a dict of raw data. Continues even if some endpoints fail."""
    if token is None:
        token = cached_access_token()
    
    # Endpoints optionnels (peuvent échouer sans bloquer l'app)
    optional_endpoints = ['customers_be', 'customers_lu', 'vendors', 'vendor_catalog', 'dim_distribution']
    
    results = {}
    endpoint_keys = list(ENDPOINTS.keys())
    failed_endpoints = []
    
    for i, key in enumerate(endpoint_keys):
        if progress_callback:
            progress_callback(i / len(endpoint_keys), f"Chargement: {key}…")
        
        try:
            results[key] = fetch_odata(key, token)
        except Exception as exc:
            _debug(f"[{key}] ÉCHEC: {exc}")
            
            # Si endpoint optionnel, continuer avec une liste vide
            if key in optional_endpoints:
                _debug(f"[{key}] Endpoint optionnel - on continue sans ces données")
                results[key] = []
                failed_endpoints.append(key)
            else:
                # Endpoint critique - on propage l'erreur
                raise RuntimeError(f"Endpoint critique '{key}' a échoué: {exc}") from exc
    
    if progress_callback:
        msg = "Données chargées ✓"
        if failed_endpoints:
            msg += f" ({len(failed_endpoints)} endpoint(s) optionnel(s) ignoré(s))"
        progress_callback(1.0, msg)
    
    return results
