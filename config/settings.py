"""
Configuration settings for Java Distribution Reporting App.
Priorité de lecture: variables d'environnement -> Streamlit secrets -> valeur par défaut.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Read a config value from env vars or Streamlit secrets."""
    val = os.getenv(key, "")
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


# ── Azure AD / Business Central ──────────────────────────────────────
BC_TENANT_ID = _get_secret("BC_TENANT_ID", "ad140881-5aae-4f5d-8941-89111ecfcdcc")
BC_CLIENT_ID = _get_secret("BC_CLIENT_ID")
BC_CLIENT_SECRET = _get_secret("BC_CLIENT_SECRET")
BC_SCOPE = _get_secret("BC_SCOPE", "https://api.businesscentral.dynamics.com/.default")

# Configuration Business Central demandée pour déploiement cloud
BC_ENVIRONMENT = _get_secret("BC_ENVIRONMENT", "Production")
BC_COMPANY = _get_secret("BC_COMPANY", "JAVA Distribution")
BC_COMPANY_BE = _get_secret("BC_COMPANY_BE", BC_COMPANY)

BC_BASE_URL = f"https://api.businesscentral.dynamics.com/v2.0/{BC_TENANT_ID}/{BC_ENVIRONMENT}/ODataV4"
BC_COMPANY_ENCODED = BC_COMPANY
BC_COMPANY_BE_ENCODED = BC_COMPANY_BE

# ── OData Endpoints ──────────────────────────────────────────────────
# Les clés historiques LU/BE sont conservées pour compatibilité avec le processing existant.
COMPANIES = {
    "JAVA LU": BC_COMPANY_ENCODED,
    "JAVA BE": BC_COMPANY_BE_ENCODED,
}

ENDPOINTS = {
    "value_entries_lu": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA LU']}')/ValueEntriesP5802?$filter=Posting_Date ge 2026-01-01",
    "value_entries_be": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA BE']}')/ValueEntriesP5802?$filter=Posting_Date ge 2026-01-01",
    "psi_lu": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA LU']}')/PostedSalesInvoicesP143?$filter=Posting_Date ge 2025-01-01",
    "psc_lu": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA LU']}')/PostedSalesCreditMemosP144?$filter=Posting_Date ge 2025-01-01",
    "psi_be": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA BE']}')/PostedSalesInvoicesP143?$filter=Posting_Date ge 2025-01-01",
    "psc_be": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA BE']}')/PostedSalesCreditMemosP144?$filter=Posting_Date ge 2025-01-01",
    "items": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA LU']}')/Fiche_article_Excel",
    "dim_distribution": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA LU']}')/Def_dim?$filter=Table_ID eq 27 and Dimension_Code eq 'ACTIVITÉ' and Dimension_Value_Code eq 'DISTRIBUTION'",
    #"customers_be": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA BE']}')/Customer",
    #"customers_lu": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA LU']}')/Customer",
    "vendor_catalog": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA LU']}')/Item_Vendor_catalog",
    #"vendors": f"{BC_BASE_URL}/Company('{COMPANIES['JAVA LU']}')/VendorCard",
}

# ── Data paths ────────────────────────────────────────────────────────
VE_FIGE_2025_PATH = os.getenv("VE_FIGE_2025_PATH", "data/VE_Fige_2025.xlsx")
CONSOLIDATED_FILE = os.getenv("CONSOLIDATED_FILE", "data/CONSOLIDE1.xlsx")

# ── IntercoCustomers (static reference) ──────────────────────────────
INTERCO_CUSTOMERS = [
    {"Company": "JAVA LU", "Sell_to_Customer_No": "C376"},
    {"Company": "JAVA BE", "Sell_to_Customer_No": "C000200"},
]

# ── App settings ──────────────────────────────────────────────────────
APP_TITLE = "Java Distribution — Reporting"
APP_ICON = "☕"
CACHE_TTL = 3600  # seconds
DATE_RANGE_START = 2025
DATE_RANGE_END = 2030

# ── Formatting ────────────────────────────────────────────────────────
CURRENCY_FORMAT = "{:,.0f} €"
PCT_FORMAT = "{:.1%}"
QTY_FORMAT = "{:,.0f}"

# ── Color palette ─────────────────────────────────────────────────────
COLORS = {
    "primary": "#1B4F72",
    "secondary": "#2E86C1",
    "success": "#27AE60",
    "danger": "#E74C3C",
    "warning": "#F39C12",
    "info": "#3498DB",
    "java_lu": "#1B4F72",
    "java_be": "#E67E22",
    "chart_palette": [
        "#1B4F72", "#E67E22", "#27AE60", "#E74C3C", "#9B59B6",
        "#3498DB", "#F39C12", "#1ABC9C", "#E91E63", "#795548",
    ],
}
