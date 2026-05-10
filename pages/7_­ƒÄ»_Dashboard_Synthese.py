"""
Page 7 — Dashboard de Synthèse
Vue globale avec KPIs principaux, tendances et répartitions.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.measures import (
    revenue_external, cogs_external, gross_margin_external,
    margin_pct_external, qty_sold_external, _external_mask,
)
from utils.ui_helpers import (
    sidebar_filters, bar_chart, line_chart, pie_chart,
    display_dataframe, kpi_row, waterfall_chart,
)
from config.settings import COLORS

st.set_page_config(page_title="Dashboard Synthèse", page_icon="🎯", layout="wide")

st.title("🎯 Dashboard de Synthèse — Java Distribution")
st.markdown("*Vue consolidée des indicateurs clés de performance*")

if "enriched_df" not in st.session_state:
    st.warning("⚠️ Veuillez d'abord charger les données depuis la page d'accueil.")
    st.stop()

df = st.session_state["enriched_df"]
filtered = sidebar_filters(df, key_prefix="p7", show_distribution=False)

if filtered.empty:
    st.info("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

mask_ext = _external_mask(filtered)
ext_data = filtered[mask_ext].copy()

# ═══════════════════════════════════════════════════════════════════════
#  TOP KPIs
# ═══════════════════════════════════════════════════════════════════════
rev = ext_data["Sales_Amount_Actual"].sum()
cogs = -ext_data["Cost_Amount_Actual"].sum()
gm = rev - cogs
margin = gm / rev if rev else 0
qty = -ext_data["Invoiced_Quantity"].sum()

# YoY comparison
years = sorted(ext_data["Posting_Year"].dropna().unique())
delta_rev, delta_gm = None, None
if len(years) >= 2:
    y_prev, y_curr = years[-2], years[-1]
    rev_p = ext_data.loc[ext_data["Posting_Year"] == y_prev, "Sales_Amount_Actual"].sum()
    rev_c = ext_data.loc[ext_data["Posting_Year"] == y_curr, "Sales_Amount_Actual"].sum()
    delta_rev = (rev_c - rev_p) / abs(rev_p) if rev_p else None
    cogs_p = -ext_data.loc[ext_data["Posting_Year"] == y_prev, "Cost_Amount_Actual"].sum()
    gm_p = rev_p - cogs_p
    gm_c = rev_c - (-ext_data.loc[ext_data["Posting_Year"] == y_curr, "Cost_Amount_Actual"].sum())
    delta_gm = (gm_c - gm_p) / abs(gm_p) if gm_p else None

kpi_row([
    ("💰 Revenue External", rev, "currency", delta_rev, "pct"),
    ("📦 COGS External", cogs, "currency"),
    ("📈 Marge Brute", gm, "currency", delta_gm, "pct"),
    ("📊 Marge %", margin, "pct"),
    ("🔢 Quantité vendue", qty, "qty"),
])

st.divider()

# ═══════════════════════════════════════════════════════════════════════
#  ROW 1: Monthly trend + Company split
# ═══════════════════════════════════════════════════════════════════════
col1, col2 = st.columns([2, 1])

month_names = {1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Jun",
               7: "Jul", 8: "Aoû", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc"}

with col1:
    st.markdown("#### 📉 Évolution mensuelle du Revenue")
    monthly = ext_data.groupby(["Posting_Month", "Posting_Year"]).agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index()
    monthly["Mois"] = monthly["Posting_Month"].map(month_names)
    monthly["Année"] = monthly["Posting_Year"].astype(int).astype(str)
    monthly = monthly.sort_values("Posting_Month")

    fig_trend = bar_chart(monthly, x="Mois", y="Revenue", color="Année",
                          title="", height=400)
    st.plotly_chart(fig_trend, use_container_width=True)

with col2:
    st.markdown("#### 🏢 Répartition par Société")
    company_rev = ext_data.groupby("Company").agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index()
    fig_pie = pie_chart(company_rev, names="Company", values="Revenue", title="", height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════
#  ROW 2: Waterfall + Location
# ═══════════════════════════════════════════════════════════════════════
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### 💧 Décomposition Revenue → Marge")
    fig_wf = waterfall_chart(
        labels=["Revenue", "COGS", "Marge Brute"],
        values=[rev, -cogs, gm],
        title="",
        height=400,
    )
    st.plotly_chart(fig_wf, use_container_width=True)

with col4:
    st.markdown("#### 📍 Revenue par Emplacement")
    loc_rev = ext_data.groupby("Location_Code_final").agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index().sort_values("Revenue", ascending=True).tail(10)

    fig_loc = bar_chart(loc_rev, x="Revenue", y="Location_Code_final",
                        title="", orientation="h", height=400)
    st.plotly_chart(fig_loc, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════
#  ROW 3: Top Vendors + Top Brands
# ═══════════════════════════════════════════════════════════════════════
col5, col6 = st.columns(2)

with col5:
    st.markdown("#### 🏭 Top 10 Fournisseurs")
    vendor_rev = ext_data.groupby("Vendor_Name").agg(
        Revenue=("Sales_Amount_Actual", "sum"),
        Cost=("Cost_Amount_Actual", "sum"),
    ).reset_index()
    vendor_rev["GM"] = vendor_rev["Revenue"] + vendor_rev["Cost"]
    vendor_rev["Margin"] = np.where(vendor_rev["Revenue"] != 0, vendor_rev["GM"] / vendor_rev["Revenue"], 0)
    top10_v = vendor_rev.nlargest(10, "Revenue")

    fig_v = bar_chart(top10_v, x="Vendor_Name", y="Revenue",
                      title="", height=400)
    fig_v.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_v, use_container_width=True)

with col6:
    st.markdown("#### 🏷️ Top 10 Marques")
    brand_rev = ext_data.groupby("Marque_NSI").agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index()
    top10_b = brand_rev.nlargest(10, "Revenue")

    fig_b = bar_chart(top10_b, x="Marque_NSI", y="Revenue",
                      title="", height=400)
    fig_b.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_b, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════
#  ROW 4: Top Customers + Margin analysis
# ═══════════════════════════════════════════════════════════════════════
col7, col8 = st.columns(2)

with col7:
    st.markdown("#### 👥 Top 10 Clients")
    cust_rev = ext_data.groupby("Sell_to_Customer_Name").agg(
        Revenue=("Sales_Amount_Actual", "sum"),
    ).reset_index().nlargest(10, "Revenue")

    fig_c = bar_chart(cust_rev, x="Sell_to_Customer_Name", y="Revenue",
                      title="", height=400)
    fig_c.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_c, use_container_width=True)

with col8:
    st.markdown("#### 📊 Marge % par Société")
    margin_by_company = ext_data.groupby("Company").agg(
        Revenue=("Sales_Amount_Actual", "sum"),
        Cost=("Cost_Amount_Actual", "sum"),
    ).reset_index()
    margin_by_company["GM"] = margin_by_company["Revenue"] + margin_by_company["Cost"]
    margin_by_company["Margin %"] = np.where(
        margin_by_company["Revenue"] != 0,
        margin_by_company["GM"] / margin_by_company["Revenue"],
        0,
    )

    fig_gauge = go.Figure()
    for i, row in margin_by_company.iterrows():
        fig_gauge.add_trace(go.Indicator(
            mode="gauge+number",
            value=row["Margin %"] * 100,
            title={"text": row["Company"]},
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 50]},
                "bar": {"color": COLORS["chart_palette"][i % len(COLORS["chart_palette"])]},
                "steps": [
                    {"range": [0, 15], "color": "#ffcccc"},
                    {"range": [15, 30], "color": "#ffffcc"},
                    {"range": [30, 50], "color": "#ccffcc"},
                ],
            },
            domain={"row": 0, "column": i},
        ))

    fig_gauge.update_layout(
        grid={"rows": 1, "columns": len(margin_by_company), "pattern": "independent"},
        height=300,
        margin=dict(t=40, b=20),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════
#  SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### 📋 Résumé par Société et Année")

summary = ext_data.groupby(["Company", "Posting_Year"]).agg(
    Revenue=("Sales_Amount_Actual", "sum"),
    Cost=("Cost_Amount_Actual", "sum"),
    Qty=("Invoiced_Quantity", lambda x: -x.sum()),
    Nb_Docs=("Key_Company_Doc", "nunique"),
).reset_index()
summary["GM"] = summary["Revenue"] + summary["Cost"]
summary["Margin %"] = np.where(summary["Revenue"] != 0, summary["GM"] / summary["Revenue"], 0)
summary = summary.rename(columns={
    "Revenue": "Revenue External",
    "Cost": "COGS (neg)",
    "GM": "Marge Brute",
    "Qty": "Quantité vendue",
    "Nb_Docs": "Nb Documents",
})

display_dataframe(summary, key="p7_summary")
