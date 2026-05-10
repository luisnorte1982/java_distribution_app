"""
Page 2 — DIS YTD Monthly External Revenue
Revenue cumulé YTD Distribution par client et fournisseur.
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.measures import _external_mask
from utils.ui_helpers import sidebar_filters, bar_chart, line_chart, display_dataframe, kpi_row

st.set_page_config(page_title="DIS YTD Monthly External Rev", page_icon="📈", layout="wide")

st.title("📈 DIS YTD Monthly External Revenue")
st.markdown("*Revenue cumulé YTD de l'activité **DISTRIBUTION** par client et fournisseur*")

if "enriched_df" not in st.session_state:
    st.warning("⚠️ Veuillez d'abord charger les données depuis la page d'accueil.")
    st.stop()

df = st.session_state["enriched_df"]
filtered = sidebar_filters(df, key_prefix="p2", show_distribution=True)

if filtered.empty:
    st.info("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

mask_ext = _external_mask(filtered)
ext_data = filtered[mask_ext].copy()

# ── KPIs ─────────────────────────────────────────────────────────────
total_rev = ext_data["Sales_Amount_Actual"].sum()
kpi_row([
    ("Revenue External YTD", total_rev, "currency"),
    ("Nb Clients", ext_data["Sell_to_Customer_Name"].nunique(), "qty"),
    ("Nb Fournisseurs", ext_data["Vendor_Name"].nunique(), "qty"),
])

st.divider()

# ── Pivot: Customer × Vendor with monthly columns ────────────────────
st.markdown("### 📋 Revenue YTD par Client × Fournisseur")

monthly = ext_data.groupby(
    ["Sell_to_Customer_Name", "Vendor_Name", "Posting_Month", "Posting_Year"], dropna=False
).agg(Revenue_External=("Sales_Amount_Actual", "sum")).reset_index()

if not monthly.empty:
    # Create Month-Year label
    month_names = {1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Jun",
                   7: "Jul", 8: "Aoû", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc"}
    monthly["Mois_Label"] = monthly["Posting_Month"].map(month_names)

    # Pivot
    pivot = monthly.pivot_table(
        index=["Sell_to_Customer_Name", "Vendor_Name"],
        columns=["Posting_Month"],
        values="Revenue_External",
        aggfunc="sum",
        fill_value=0,
    )
    pivot.columns = [month_names.get(int(c), str(c)) for c in pivot.columns]

    # Add total
    pivot["Total YTD"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total YTD", ascending=False).reset_index()

    display_dataframe(pivot, title="", key="p2_ytd_table")

    # ── Chart: YTD by Customer ───────────────────────────────────────
    st.markdown("### 📊 Top 15 Clients — Revenue YTD")
    cust_total = ext_data.groupby("Sell_to_Customer_Name").agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index().nlargest(15, "Revenue")

    fig = bar_chart(cust_total, x="Sell_to_Customer_Name", y="Revenue",
                    title="Top 15 Clients — Revenue External YTD", height=500)
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # ── Chart: Monthly trend ─────────────────────────────────────────
    st.markdown("### 📉 Évolution mensuelle du Revenue")
    monthly_trend = ext_data.groupby(["Posting_Month", "Company"]).agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index()
    monthly_trend["Mois"] = monthly_trend["Posting_Month"].map(month_names)
    monthly_trend = monthly_trend.sort_values("Posting_Month")

    fig2 = line_chart(monthly_trend, x="Mois", y="Revenue", color="Company",
                      title="Revenue mensuel par société")
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Aucune donnée YTD disponible.")
