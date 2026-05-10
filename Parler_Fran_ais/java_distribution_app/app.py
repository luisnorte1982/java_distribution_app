"""
Java Distribution — Reporting Application
Main entry point and data loading page.
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import (
    APP_TITLE, APP_ICON, BC_CLIENT_ID, BC_TENANT_ID,
    CONSOLIDATED_FILE, INTERCO_CUSTOMERS, COLORS,
)
from utils.data_processor import (
    load_from_excel, build_interco_table, build_date_table,
    build_enriched_fact_table, raw_to_dataframes,
)
from utils.measures import revenue_external, gross_margin_external, margin_pct_external

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════
#  CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1B4F72 0%, #2E86C1 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white !important; margin: 0; }
    .main-header p { color: #D5E8D4; margin: 0.5rem 0 0 0; }

    /* KPI cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem;
        font-weight: 700;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #F0F4F8;
    }

    /* Table improvements */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* Status badges */
    .status-connected { color: #27AE60; font-weight: bold; }
    .status-demo { color: #F39C12; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>☕ Java Distribution — Reporting</h1>
    <p>Tableau de bord des revenus et marges — Business Central</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
#  SIDEBAR — DATA SOURCE & CONNECTION
# ═══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/coffee-beans-.png", width=60)
    st.markdown("## ☕ Java Distribution")
    st.divider()

    default_mode_index = 0 if os.path.exists(CONSOLIDATED_FILE) else 1
    data_mode = st.radio(
        "Source de données",
        ["📊 Données Excel (démo)", "🔗 Business Central (live)"],
        index=default_mode_index,
        key="data_source_selector",
        help="En cloud, si aucun fichier Excel local n'est présent, le mode Business Central est sélectionné par défaut.",
    )

    if "🔗" in data_mode:
        st.markdown("### 🔐 Connexion Business Central")
        client_id = st.text_input("Client ID", value=BC_CLIENT_ID or "", type="password", key="bc_cid")
        client_secret = st.text_input("Client Secret", type="password", key="bc_secret")
        if client_id and client_secret:
            os.environ["BC_CLIENT_ID"] = client_id
            os.environ["BC_CLIENT_SECRET"] = client_secret
            st.success("✅ Credentials configurées")
        else:
            st.info("Renseignez vos credentials Azure AD")

    st.divider()
    st.markdown("### 📁 Fichiers optionnels (mode démo)")

    uploaded_consolidated = st.file_uploader(
        "CONSOLIDE1.xlsx (optionnel)", type=["xlsx"], key="consolidated_upload"
    )
    if uploaded_consolidated:
        st.session_state["uploaded_consolidated_bytes"] = uploaded_consolidated.getvalue()
        st.success("✅ Fichier CONSOLIDE1.xlsx prêt à être chargé (session courante).")

    uploaded_file = st.file_uploader(
        "VE_Fige_2025.xlsx (optionnel)", type=["xlsx"], key="ve_upload"
    )
    if uploaded_file:
        os.makedirs("data", exist_ok=True)
        save_path = os.path.join("data", "VE_Fige_2025.xlsx")
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        st.success(f"✅ Fichier sauvegardé: {save_path}")

# ═══════════════════════════════════════════════════════════════════════
#  DATA LOADING
# ═══════════════════════════════════════════════════════════════════════


def load_and_process_excel(path: str) -> dict:
    """Load Excel data as dict of DataFrames (one per sheet, no headers)."""
    sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl", header=None)
    return sheets


def build_enriched_from_sheets(sheets: dict) -> pd.DataFrame:
    """
    Build an enriched DataFrame from the Excel pivot table sheets.
    Parses the exact TCD layout of CONSOLIDE1.xlsx.
    """
    all_rows = []

    # ── Sheet 1: DIS Monthly external rev ────────────────────────────
    # Layout: row6=[Company, Name, Marque_NSI, RevExt 2025, GM 2025, RevExt 2026, GM 2026, ...]
    # row5 has years: 2025, 2026
    if "DIS Monthly external rev" in sheets:
        raw = sheets["DIS Monthly external rev"]
        # Row 6 (0-indexed) has column headers; row 5 has year; data starts row 7
        # Get the slicer month from row 2 col 1
        slicer_month = _safe_int(raw.iloc[2, 1]) or 4

        # Row 5: years → cols 3=2025, 5=2026
        # Row 6: Company | Name | Marque_NSI | Revenue External | Gross Margin External | Revenue External | Gross Margin External
        year_row = raw.iloc[5].values  # 2025, NaN, 2026, NaN
        header_row = raw.iloc[6].values

        # Map col_idx → (year, measure)
        col_map = {}
        current_year = None
        for ci in range(3, len(header_row)):
            yr = year_row[ci] if ci < len(year_row) else None
            if pd.notna(yr):
                current_year = _safe_int(yr)
            h = str(header_row[ci]).strip() if ci < len(header_row) and pd.notna(header_row[ci]) else ""
            if current_year and h:
                is_gm = "gross" in h.lower() or "margin" in h.lower()
                col_map[ci] = (current_year, "gm" if is_gm else "rev")

        # Group col_map by year: {year: {"rev": ci, "gm": ci}}
        year_cols = {}
        for ci, (year, measure) in col_map.items():
            year_cols.setdefault(year, {})[measure] = ci

        last_company = ""
        for ri in range(7, len(raw)):
            row = raw.iloc[ri]
            co = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if co and co.lower() not in ["total", "grand total", "nan"]:
                last_company = co
            vendor = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            brand = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
            if not vendor:
                continue

            for year, measures in year_cols.items():
                rev_ci = measures.get("rev")
                gm_ci = measures.get("gm")
                rev_val = _safe_float(row.iloc[rev_ci]) if rev_ci is not None and rev_ci < len(row) else 0
                gm_val = _safe_float(row.iloc[gm_ci]) if gm_ci is not None and gm_ci < len(row) else 0
                if rev_val == 0 and gm_val == 0:
                    continue
                r = _base_row()
                r["Company"] = last_company
                r["Vendor_Name"] = vendor
                r["Marque_NSI"] = brand
                r["Posting_Year"] = year
                r["Posting_Month"] = slicer_month
                r["Dimension_Value_Code"] = "DISTRIBUTION"
                r["_source"] = "dis_monthly"
                r["Sales_Amount_Actual"] = rev_val
                # COGS = Rev - GM → Cost_Amount_Actual = -(Rev - GM) = GM - Rev
                r["Cost_Amount_Actual"] = -(rev_val - gm_val) if rev_val != 0 else 0
                all_rows.append(r)

    # ── Sheet 2: DIS YTD Monthly external rev ────────────────────────
    # Row 3: headers [Revenue External, NaN, Mois, Année, Company, NaN]
    # Row 4: months  [NaN, NaN, 1, 2, 3, 4]
    # Row 5: years   [NaN, NaN, 2026, 2026, 2026, 2026]
    # Row 6: data headers [Sell_to_Customer_Name, Name(vendor), company1, company2, ...]
    # Actually layout: row3=[Revenue External, NaN, Mois, Année, Company]; row4=[NaN,NaN,1,2,3,4]; row5=[NaN,NaN,2026,2026,2026,2026]
    # Then data rows: Customer_name | Vendor | values per month
    if "DIS YTD Monthly external rev" in sheets:
        raw = sheets["DIS YTD Monthly external rev"]
        # Months in row index 4 (0-based in the sheet, but sheet starts at row 0)
        months_row = raw.iloc[4].values  # col2 onwards: 1,2,3,4
        years_row = raw.iloc[5].values   # col2 onwards: 2026,2026,...

        col_map_ytd = {}
        for ci in range(2, len(months_row)):
            m = _safe_int(months_row[ci])
            y = _safe_int(years_row[ci]) if ci < len(years_row) else None
            if m and y:
                col_map_ytd[ci] = (y, m)

        last_customer = ""
        for ri in range(6, len(raw)):
            row = raw.iloc[ri]
            cust = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if cust and cust.lower() not in ["total", "grand total", "nan"]:
                last_customer = cust
            vendor = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            if not last_customer and not vendor:
                continue

            for ci, (year, month) in col_map_ytd.items():
                val = _safe_float(row.iloc[ci]) if ci < len(row) else 0
                if val == 0:
                    continue
                r = _base_row()
                r["Sell_to_Customer_Name"] = last_customer
                r["Vendor_Name"] = vendor if vendor else last_customer
                r["Posting_Year"] = year
                r["Posting_Month"] = month
                r["Dimension_Value_Code"] = "DISTRIBUTION"
                r["_source"] = "dis_ytd"
                r["Sales_Amount_Actual"] = val
                all_rows.append(r)

    # ── Sheet 3: Rev salesP by location ──────────────────────────────
    # Row 5: header [Revenue External, NaN, NaN, Année]
    # Row 6: [NaN, NaN, NaN, 2026]
    # Row 7: [Company, Location_Code, Marque_NSI, Revenue External]
    if "Rev salesP by location" in sheets:
        raw = sheets["Rev salesP by location"]
        slicer_month = _safe_int(raw.iloc[3, 1]) or 4  # Mois slicer

        # Find data header row
        year_val = _safe_int(raw.iloc[6, 3]) if len(raw) > 6 else 2026

        last_company = ""
        last_location = ""
        for ri in range(7, len(raw)):
            row = raw.iloc[ri]
            co = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if co and co.lower() not in ["total", "grand total", "nan"]:
                last_company = co
            loc = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            if loc and loc.lower() not in ["total", "grand total", "nan"]:
                last_location = loc
            brand = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
            val = _safe_float(row.iloc[3]) if len(row) > 3 else 0

            if not brand or val == 0:
                continue

            r = _base_row()
            r["Company"] = last_company
            r["Location_Code_final"] = last_location
            r["Marque_NSI"] = brand
            r["Sales_Amount_Actual"] = val
            r["Posting_Year"] = year_val or 2026
            r["Posting_Month"] = slicer_month
            r["Dimension_Value_Code"] = "DISTRIBUTION"
            r["_source"] = "location"
            all_rows.append(r)

    # ── Sheet 4: ALL Monthly external rev ────────────────────────────
    # Row 5: [Company, Location_Code, 2025, 2026]
    if "ALL Monthly external rev" in sheets:
        raw = sheets["ALL Monthly external rev"]
        slicer_month = _safe_int(raw.iloc[4, 2]) or 4
        # Year headers in row 5
        year_headers = {}
        for ci in range(2, min(len(raw.columns), 20)):
            yr = _safe_int(raw.iloc[5, ci])
            if yr:
                year_headers[ci] = yr

        last_company = ""
        for ri in range(6, len(raw)):
            row = raw.iloc[ri]
            co = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if co and co.lower() not in ["total", "grand total", "nan"]:
                last_company = co
            loc = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""

            for ci, yr in year_headers.items():
                val = _safe_float(row.iloc[ci]) if ci < len(row) else 0
                if val == 0:
                    continue
                r = _base_row()
                r["Company"] = last_company
                r["Location_Code_final"] = loc
                r["Sales_Amount_Actual"] = val
                r["Posting_Year"] = yr
                r["Posting_Month"] = slicer_month
                r["_source"] = "all_monthly"
                all_rows.append(r)

    # ── Sheet 5: Rev by vendor name YTD ──────────────────────────────
    # Row 5: [NaN, 1, NaN, 2, NaN, 3, NaN, 4, NaN]  (months)
    # Row 6: [Name, 2025, 2026, 2025, 2026, 2025, 2026, 2025, 2026]
    if "Rev by vendor name YTD" in sheets:
        raw = sheets["Rev by vendor name YTD"]
        months_row = raw.iloc[5].values
        years_row = raw.iloc[6].values

        col_map_vy = {}
        current_month = None
        for ci in range(1, len(years_row)):
            m = _safe_int(months_row[ci])
            if m:
                current_month = m
            yr = _safe_int(years_row[ci])
            if yr and current_month:
                col_map_vy[ci] = (yr, current_month)

        for ri in range(7, len(raw)):
            row = raw.iloc[ri]
            vendor = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if not vendor or vendor.lower() in ["total", "grand total", "nan"]:
                continue

            for ci, (year, month) in col_map_vy.items():
                val = _safe_float(row.iloc[ci]) if ci < len(row) else 0
                if val == 0:
                    continue
                r = _base_row()
                r["Vendor_Name"] = vendor
                r["Sales_Amount_Actual"] = val
                r["Posting_Year"] = year
                r["Posting_Month"] = month
                r["_source"] = "vendor_ytd"
                all_rows.append(r)

    # ── Sheet 6: Revenue by salesperson ──────────────────────────────
    # Row 5: [NaN, NaN, 2026, NaN, NaN, ...]
    # Row 6: [NaN, NaN, 1, NaN, 2, NaN, 3, NaN, 4, NaN]  (months)
    # Row 7: [Sell_to_Customer_Name, Description, Revenue External, Gross Margin External, ...]
    if "Revenue by salesperson" in sheets:
        raw = sheets["Revenue by salesperson"]
        year_row_sp = raw.iloc[5].values
        month_row_sp = raw.iloc[6].values
        header_row_sp = raw.iloc[7].values

        # Build col map: ci → (year, month, measure_type)
        sp_year = _safe_int(year_row_sp[2]) or 2026
        col_map_sp = {}
        current_month_sp = None
        for ci in range(2, len(header_row_sp)):
            m = _safe_int(month_row_sp[ci])
            if m:
                current_month_sp = m
            h = str(header_row_sp[ci]).strip() if ci < len(header_row_sp) and pd.notna(header_row_sp[ci]) else ""
            if current_month_sp and h:
                is_gm = "gross" in h.lower() or "margin" in h.lower()
                col_map_sp[ci] = (sp_year, current_month_sp, "gm" if is_gm else "rev")

        # Group by (year, month): {"rev": ci, "gm": ci}
        sp_month_cols = {}
        for ci, (year, month, measure) in col_map_sp.items():
            sp_month_cols.setdefault((year, month), {})[measure] = ci

        last_customer = ""
        for ri in range(8, len(raw)):
            row = raw.iloc[ri]
            cust = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            if cust and cust.lower() not in ["total", "grand total", "nan"]:
                last_customer = cust
            desc = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            if not last_customer and not desc:
                continue

            for (year, month), measures in sp_month_cols.items():
                rev_ci = measures.get("rev")
                gm_ci = measures.get("gm")
                rev_val = _safe_float(row.iloc[rev_ci]) if rev_ci is not None and rev_ci < len(row) else 0
                gm_val = _safe_float(row.iloc[gm_ci]) if gm_ci is not None and gm_ci < len(row) else 0
                if rev_val == 0 and gm_val == 0:
                    continue
                r = _base_row()
                r["Sell_to_Customer_Name"] = last_customer
                r["Description"] = desc
                r["Posting_Year"] = year
                r["Posting_Month"] = month
                r["_source"] = "salesperson"
                r["Sales_Amount_Actual"] = rev_val
                r["Cost_Amount_Actual"] = -(rev_val - gm_val) if rev_val != 0 else 0
                all_rows.append(r)

    if not all_rows:
        return pd.DataFrame()

    enriched = pd.DataFrame(all_rows)

    # Ensure types
    for col in ["Sales_Amount_Actual", "Cost_Amount_Actual", "Invoiced_Quantity"]:
        if col in enriched.columns:
            enriched[col] = pd.to_numeric(enriched[col], errors="coerce").fillna(0)

    enriched["Posting_Year"] = pd.to_numeric(enriched["Posting_Year"], errors="coerce")
    enriched["Posting_Month"] = pd.to_numeric(enriched["Posting_Month"], errors="coerce").fillna(1).astype(int)

    enriched["IsInterco_computed"] = False
    enriched["Key_Company_Doc"] = ""
    enriched["Posting_Quarter"] = "T" + np.ceil(enriched["Posting_Month"] / 3).astype(int).astype(str)

    month_names_short = {1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Jun",
                         7: "Jul", 8: "Aoû", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc"}
    enriched["Mois court"] = enriched["Posting_Month"].map(month_names_short)

    # Create Posting_Date from year+month
    enriched["Posting_Date"] = pd.to_datetime(
        enriched["Posting_Year"].astype(int).astype(str) + "-" +
        enriched["Posting_Month"].astype(int).astype(str).str.zfill(2) + "-01",
        errors="coerce",
    )

    # Fill missing columns
    for col in ["Company", "Vendor_Name", "Marque_NSI", "Description",
                 "Sell_to_Customer_Name", "Salesperson_Code",
                 "Location_Code_final", "Dimension_Value_Code", "Item_No"]:
        if col not in enriched.columns:
            enriched[col] = ""

    return enriched


def _base_row() -> dict:
    """Return a template row dict with default values."""
    return {
        "Sales_Amount_Actual": 0,
        "Cost_Amount_Actual": 0,
        "Invoiced_Quantity": 0,
        "Posting_Year": 2026,
        "Posting_Month": 1,
        "Company": "",
        "Vendor_Name": "",
        "Marque_NSI": "",
        "Description": "",
        "Sell_to_Customer_Name": "",
        "Salesperson_Code": "",
        "Location_Code_final": "",
        "Dimension_Value_Code": "",
        "Item_No": "",
        "_source": "",
    }


def _safe_float(v) -> float:
    if pd.isna(v):
        return 0.0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def _safe_int(v):
    if pd.isna(v):
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════════════════
#  LOAD DATA BUTTON
# ═══════════════════════════════════════════════════════════════════════

col_load1, col_load2, col_load3 = st.columns([1, 2, 1])

with col_load2:
    if "🔗" in data_mode:
        load_btn = st.button("🔄 Charger depuis Business Central", type="primary", use_container_width=True)
        if load_btn:
            with st.spinner("Connexion à Business Central et chargement des données…"):
                try:
                    from utils.odata_client import fetch_all_endpoints, cached_access_token
                    raw = fetch_all_endpoints()
                    frames = raw_to_dataframes(raw)
                    enriched = build_enriched_fact_table(frames)
                    st.session_state["enriched_df"] = enriched
                    st.session_state["frames"] = frames
                    st.session_state["loaded_data_mode"] = "odata"
                    st.success(f"✅ Données chargées : {len(enriched):,} lignes")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur de connexion : {e}")
    else:
        load_btn = st.button("📊 Charger les données Excel", type="primary", use_container_width=True)
        if load_btn:
            with st.spinner("Chargement du fichier Excel…"):
                excel_path = CONSOLIDATED_FILE

                if "uploaded_consolidated_bytes" in st.session_state:
                    os.makedirs("data", exist_ok=True)
                    uploaded_path = os.path.join("data", "CONSOLIDE1_uploaded.xlsx")
                    with open(uploaded_path, "wb") as f:
                        f.write(st.session_state["uploaded_consolidated_bytes"])
                    excel_path = uploaded_path

                if os.path.exists(excel_path):
                    sheets = load_and_process_excel(excel_path)
                    enriched = build_enriched_from_sheets(sheets)
                    if not enriched.empty:
                        st.session_state["enriched_df"] = enriched
                        st.session_state["sheets"] = sheets
                        st.session_state["loaded_data_mode"] = "excel"
                        st.success(f"✅ Données Excel chargées : {len(enriched):,} lignes")
                        st.rerun()
                    else:
                        st.error("❌ Impossible de parser les données Excel.")
                else:
                    st.error("❌ Aucun fichier Excel disponible. Chargez CONSOLIDE1.xlsx ou utilisez le mode Business Central.")

# ═══════════════════════════════════════════════════════════════════════
#  DATA STATUS & OVERVIEW
# ═══════════════════════════════════════════════════════════════════════

if "enriched_df" in st.session_state and not st.session_state["enriched_df"].empty:
    df = st.session_state["enriched_df"]
    mode = st.session_state.get("loaded_data_mode", "excel")

    st.divider()

    mode_badge = "🟢 Business Central (live)" if mode == "odata" else "🟡 Excel (démo)"
    st.markdown(f"**Statut :** {mode_badge} — **{len(df):,}** lignes chargées")

    # Quick KPIs
    from utils.measures import _external_mask
    mask = _external_mask(df)
    rev = df.loc[mask, "Sales_Amount_Actual"].sum()
    cogs_val = -df.loc[mask, "Cost_Amount_Actual"].sum()
    gm = rev - cogs_val
    margin = gm / rev if rev else 0

    st.markdown("### 📊 Aperçu rapide")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue External", f"{rev:,.0f} €")
    c2.metric("COGS External", f"{cogs_val:,.0f} €")
    c3.metric("Marge Brute", f"{gm:,.0f} €")
    c4.metric("Marge %", f"{margin:.1%}")

    st.divider()

    # Data summary
    st.markdown("### 📋 Résumé des données")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Dimensions disponibles :**")
        dims = {
            "Sociétés": df["Company"].nunique() if "Company" in df.columns else 0,
            "Fournisseurs": df["Vendor_Name"].nunique() if "Vendor_Name" in df.columns else 0,
            "Marques": df["Marque_NSI"].nunique() if "Marque_NSI" in df.columns else 0,
            "Clients": df["Sell_to_Customer_Name"].nunique() if "Sell_to_Customer_Name" in df.columns else 0,
            "Emplacements": df["Location_Code_final"].nunique() if "Location_Code_final" in df.columns else 0,
        }
        for k, v in dims.items():
            if v > 0:
                st.write(f"- **{k}** : {v}")

    with col_b:
        st.markdown("**Période :**")
        if "Posting_Year" in df.columns:
            years = sorted(df["Posting_Year"].dropna().unique())
            st.write(f"- **Années** : {', '.join(str(int(y)) for y in years)}")
        if "Posting_Month" in df.columns:
            months = sorted(df["Posting_Month"].dropna().unique())
            st.write(f"- **Mois** : {', '.join(str(int(m)) for m in months)}")

    st.divider()
    st.markdown("""
    ### 🧭 Navigation
    Utilisez le **menu latéral** (← gauche) pour accéder aux différentes pages :

    | Page | Description |
    |---|---|
    | 📊 **DIS Monthly External Rev** | Revenue mensuel Distribution par fournisseur/marque |
    | 📈 **DIS YTD Monthly External Rev** | Revenue YTD Distribution par client/fournisseur |
    | 📍 **Rev SalesP By Location** | Revenue par emplacement et marque |
    | 🏢 **ALL Monthly External Rev** | Revenue mensuel toutes activités par société |
    | 👤 **Revenue By Salesperson** | Détail par vendeur, client et article |
    | 🔄 **Rev By Vendor YTD** | Suivi YTD par fournisseur (N vs N-1) |
    | 🎯 **Dashboard Synthèse** | Vue consolidée des KPIs principaux |
    """)

else:
    st.markdown("""
    ---
    ### 🚀 Pour commencer

    1. **Mode Live (recommandé en cloud)** : Sélectionnez "🔗 Business Central" et renseignez vos identifiants Azure AD.
    2. **Mode Démo** : Vous pouvez charger un `CONSOLIDE1.xlsx` depuis la barre latérale si aucun fichier local n'est présent.

    Les données seront automatiquement traitées et disponibles sur toutes les pages du dashboard.
    """)

    # Show sample data info
    if os.path.exists(CONSOLIDATED_FILE):
        st.info(f"📁 Fichier Excel détecté : `{CONSOLIDATED_FILE}` — Prêt à charger !")
    elif "uploaded_consolidated_bytes" in st.session_state:
        st.info("📤 Fichier CONSOLIDE1.xlsx uploadé dans la session — prêt à charger.")
    else:
        st.warning("⚠️ Aucun fichier Excel local. En Streamlit Cloud, utilisez le mode Business Central (live) ou chargez un fichier démo.")

# ═══════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#999; font-size:0.85rem;'>"
    "☕ Java Distribution Reporting — v1.0 | Business Central OData V4 | "
    "Streamlit Dashboard</div>",
    unsafe_allow_html=True,
)
