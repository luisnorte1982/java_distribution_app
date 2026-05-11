"""
Data processing module — reproduces Power Query logic and builds the star schema.
Works with both live OData data and the consolidated Excel fallback.
"""
import os
import pandas as pd
import numpy as np
import streamlit as st
from config.settings import INTERCO_CUSTOMERS, CONSOLIDATED_FILE, VE_FIGE_2025_PATH


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize BC OData column names (remove trailing underscores)"""
    rename_map = {col: col.rstrip("_") for col in df.columns if col.endswith("_")}
    return df.rename(columns=rename_map) if rename_map else df



# ═══════════════════════════════════════════════════════════════════════
#  INTERCO TABLE
# ═══════════════════════════════════════════════════════════════════════

def build_interco_table() -> pd.DataFrame:
    """Static intercompany reference table."""
    df = pd.DataFrame(INTERCO_CUSTOMERS)
    df["Key_Company_Cust"] = df["Company"] + "|" + df["Sell_to_Customer_No"]
    return df


# ═══════════════════════════════════════════════════════════════════════
#  DATE TABLE
# ═══════════════════════════════════════════════════════════════════════

def build_date_table(start_year: int = 2025, end_year: int = 2030) -> pd.DataFrame:
    """Generate a calendar dimension table."""
    dates = pd.date_range(f"{start_year}-01-01", f"{end_year}-12-31", freq="D")
    df = pd.DataFrame({"Date": dates})
    df["Année"] = df["Date"].dt.year
    df["Mois"] = df["Date"].dt.month
    df["Nom du mois"] = df["Date"].dt.strftime("%B")
    df["Trimestre"] = "T" + df["Date"].dt.quarter.astype(str)
    df["AnnéeMois"] = df["Année"] * 100 + df["Mois"]
    df["Mois court"] = df["Date"].dt.strftime("%b")
    return df


# ═══════════════════════════════════════════════════════════════════════
#  ODATA → DATAFRAMES  (live mode)
# ═══════════════════════════════════════════════════════════════════════

def raw_to_dataframes(raw: dict[str, list[dict]]) -> dict[str, pd.DataFrame]:
    """Convert raw OData dicts to DataFrames with Power Query logic."""
    frames = {}

    # ── Value Entries ────────────────────────────────────────────────
    ve_lu = pd.DataFrame(raw["value_entries_lu"])
    ve_lu["Company"] = "JAVA LU"
    ve_be = pd.DataFrame(raw["value_entries_be"])
    ve_be["Company"] = "JAVA BE"
    ve_2026 = pd.concat([ve_lu, ve_be], ignore_index=True)
    ve_2026["Key_Company_Doc"] = ve_2026["Company"] + "|" + ve_2026["Document_No"].astype(str)
    ve_2026["IsInterco"] = False

    # Frozen 2025
    if os.path.exists(VE_FIGE_2025_PATH):
        ve_2025 = pd.read_excel(VE_FIGE_2025_PATH)
        combined_ve = pd.concat([ve_2026, ve_2025], ignore_index=True)
    else:
        combined_ve = ve_2026

    frames["combined_ve"] = combined_ve

    # ── Sales Documents ──────────────────────────────────────────────
    parts = []
    for key, company, doc_type in [
        ("psi_lu", "JAVA LU", "Invoice"),
        ("psc_lu", "JAVA LU", "Credit Memo"),
        ("psi_be", "JAVA BE", "Invoice"),
        ("psc_be", "JAVA BE", "Credit Memo"),
    ]:
        tmp = normalize_columns(pd.DataFrame(raw[key]))
        tmp["Company"] = company
        tmp["BC_DocumentType"] = doc_type
        parts.append(tmp)
    sales_docs = pd.concat(parts, ignore_index=True)
    sales_docs["Key_Company_Doc"] = sales_docs["Company"] + "|" + sales_docs["No"].astype(str)
    sales_docs["Key_Company_Cust"] = (
        sales_docs["Company"] + "|" + sales_docs["Sell_to_Customer_No"].astype(str)
    )
    frames["sales_docs"] = sales_docs

    # ── Reference tables ─────────────────────────────────────────────
    frames["items"] = normalize_columns(pd.DataFrame(raw["items"]))
    frames["vendors"] = normalize_columns(pd.DataFrame(raw["vendors"]))
    frames["dim_distribution"] = pd.DataFrame(raw["dim_distribution"])
    frames["customers_be"] = normalize_columns(pd.DataFrame(raw["customers_be"]))
    frames["customers_lu"] = normalize_columns(pd.DataFrame(raw["customers_lu"]))
    frames["vendor_catalog"] = pd.DataFrame(raw["vendor_catalog"])

    # Client list combined (distinct by Name)
    clients_combined = pd.concat(
        [frames["customers_be"], frames["customers_lu"]], ignore_index=True
    ).drop_duplicates(subset=["Name"])
    frames["client_list_belu"] = clients_combined

    # ── Interco & Date ───────────────────────────────────────────────
    frames["interco"] = build_interco_table()
    frames["date"] = build_date_table()

    return frames


# ═══════════════════════════════════════════════════════════════════════
#  BUILD ENRICHED FACT TABLE  (star schema join)
# ═══════════════════════════════════════════════════════════════════════

def build_enriched_fact_table(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Join the fact table (combined_ve) with all dimension tables
    to produce the single enriched DataFrame used by all dashboards.
    """
    df = frames["combined_ve"].copy()

    # Ensure date types
    if "Posting_Date" in df.columns:
        df["Posting_Date"] = pd.to_datetime(df["Posting_Date"], errors="coerce")

    # Ensure numeric types
    for col in ["Sales_Amount_Actual", "Cost_Amount_Actual", "Invoiced_Quantity", "Valued_Quantity"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ── Join Item list ───────────────────────────────────────────────
    items = frames["items"]
    item_cols = ["No"]
    for c in ["Description", "Marque_NSI", "Item_Category_Code", "Vendor_No", "Unit_Cost", "Unit_Price"]:
        if c in items.columns:
            item_cols.append(c)
    df = df.merge(
        items[item_cols].rename(columns={"No": "Item_No_item"}),
        left_on="Item_No", right_on="Item_No_item", how="left",
    )
    if "Item_No_item" in df.columns:
        df.drop(columns=["Item_No_item"], inplace=True)

    # ── Join Vendors ─────────────────────────────────────────────────
    vendors = frames["vendors"]
    vendor_cols = ["No"]
    for c in ["Name", "Location_Code", "Country_Region_Code"]:
        if c in vendors.columns:
            vendor_cols.append(c)
    df = df.merge(
        vendors[vendor_cols].rename(columns={"No": "Vendor_No_v", "Name": "Vendor_Name", "Location_Code": "Vendor_Location"}),
        left_on="Vendor_No", right_on="Vendor_No_v", how="left",
    )
    if "Vendor_No_v" in df.columns:
        df.drop(columns=["Vendor_No_v"], inplace=True)

    # ── Join Sales Docs ──────────────────────────────────────────────
    sd = frames["sales_docs"]
    sd_cols = ["Key_Company_Doc"]
    for c in ["Sell_to_Customer_No", "Sell_to_Customer_Name", "Salesperson_Code",
              "Location_Code", "Key_Company_Cust", "BC_DocumentType"]:
        if c in sd.columns:
            sd_cols.append(c)
    # Deduplicate sales_docs on Key_Company_Doc (keep first)
    sd_dedup = sd[sd_cols].drop_duplicates(subset=["Key_Company_Doc"], keep="first")
    df = df.merge(sd_dedup, on="Key_Company_Doc", how="left", suffixes=("", "_sd"))

    # ── Join Dimension DISTRIBUTION ──────────────────────────────────
    dim = frames["dim_distribution"]
    if not dim.empty and "No" in dim.columns:
        dim_cols = ["No"]
        if "Dimension_Value_Code" in dim.columns:
            dim_cols.append("Dimension_Value_Code")
        df = df.merge(
            dim[dim_cols].rename(columns={"No": "Item_No_dim"}),
            left_on="Item_No", right_on="Item_No_dim", how="left",
        )
        if "Item_No_dim" in df.columns:
            df.drop(columns=["Item_No_dim"], inplace=True)
    else:
        df["Dimension_Value_Code"] = np.nan

    # ── Compute IsInterco ────────────────────────────────────────────
    interco = frames["interco"]
    interco_keys = set(interco["Key_Company_Cust"].dropna())
    # Map Key_Company_Doc → Key_Company_Cust from sales_docs
    if "Key_Company_Cust" in df.columns:
        df["IsInterco_computed"] = df["Key_Company_Cust"].isin(interco_keys)
    else:
        df["IsInterco_computed"] = False

    # Also honor the original IsInterco column from frozen data
    if "IsInterco" in df.columns:
        df["IsInterco_computed"] = df["IsInterco_computed"] | df["IsInterco"].fillna(False).astype(bool)

    # ── Date enrichment ──────────────────────────────────────────────
    df["Posting_Year"] = df["Posting_Date"].dt.year
    df["Posting_Month"] = df["Posting_Date"].dt.month
    df["Posting_Quarter"] = "T" + df["Posting_Date"].dt.quarter.astype(str)
    df["AnnéeMois"] = df["Posting_Year"] * 100 + df["Posting_Month"]
    df["Mois court"] = df["Posting_Date"].dt.strftime("%b")
    df["Nom du mois"] = df["Posting_Date"].dt.strftime("%B")

    # Use Location_Code from sales_docs if available, else from VE
    if "Location_Code_sd" in df.columns:
        df["Location_Code_final"] = df["Location_Code_sd"].fillna(df.get("Location_Code", ""))
    elif "Location_Code" in df.columns:
        df["Location_Code_final"] = df["Location_Code"]
    else:
        df["Location_Code_final"] = ""

    return df


# ═══════════════════════════════════════════════════════════════════════
#  EXCEL FALLBACK  (load from CONSOLIDE1.xlsx cached data)
# ═══════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=7200, show_spinner="Chargement des données Excel…")
def load_from_excel(path: str | None = None) -> pd.DataFrame:
    """
    Load data from the consolidated Excel file and build an enriched-like
    DataFrame from sheet data. This is the DEMO / FALLBACK mode when
    OData credentials are not configured.
    """
    if path is None:
        path = CONSOLIDATED_FILE
    if not os.path.exists(path):
        return pd.DataFrame()

    sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    return sheets


def build_demo_data(path: str | None = None) -> dict:
    """
    Build demo datasets from the Excel sheets. Returns dict with
    keys matching the sheet names, plus synthesized dimension data.
    """
    sheets = load_from_excel(path)
    if not sheets:
        return {}
    return sheets


# ═══════════════════════════════════════════════════════════════════════
#  MAIN LOADER  (called by app.py)
# ═══════════════════════════════════════════════════════════════════════

def load_data(mode: str = "auto") -> dict:
    """
    Load data in the given mode:
      - 'odata': live from Business Central
      - 'excel': from CONSOLIDE1.xlsx
      - 'auto': try odata, fall back to excel
    Returns a dict with 'enriched_df' and 'frames'.
    """
    from config.settings import BC_CLIENT_ID

    if mode == "odata" or (mode == "auto" and BC_CLIENT_ID):
        try:
            from utils.odata_client import fetch_all_endpoints
            raw = fetch_all_endpoints()
            frames = raw_to_dataframes(raw)
            enriched = build_enriched_fact_table(frames)
            return {"enriched_df": enriched, "frames": frames, "mode": "odata"}
        except Exception as e:
            st.warning(f"⚠️ Connexion OData échouée : {e}. Basculement vers les données Excel.")

    # Excel fallback
    sheets = build_demo_data()
    return {"sheets": sheets, "frames": {}, "mode": "excel"}
