"""
Page 3 — Revenue by Sales Person & Location
Revenue par emplacement (entrepôt/site) et marque.
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.measures import _external_mask
from utils.ui_helpers import sidebar_filters, bar_chart, pie_chart, display_dataframe, kpi_row

st.set_page_config(page_title="Rev by Location", page_icon="📍", layout="wide")

st.title("📍 Revenue par Emplacement")
st.markdown("*Revenue par emplacement (entrepôt/site) et marque — activité **DISTRIBUTION***")

if "enriched_df" not in st.session_state:
    st.warning("⚠️ Veuillez d'abord charger les données depuis la page d'accueil.")
    st.stop()

df = st.session_state["enriched_df"]
filtered = sidebar_filters(df, key_prefix="p3", show_distribution=True)

if filtered.empty:
    st.info("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

mask_ext = _external_mask(filtered)
ext_data = filtered[mask_ext].copy()

# ── KPIs ─────────────────────────────────────────────────────────────
total_rev = ext_data["Sales_Amount_Actual"].sum()
n_locations = ext_data["Location_Code_final"].nunique()
kpi_row([
    ("Revenue External", total_rev, "currency"),
    ("Nb Emplacements", n_locations, "qty"),
    ("Nb Marques", ext_data["Marque_NSI"].nunique(), "qty"),
])

st.divider()

# ── Table: Company × Location × Brand ───────────────────────────────
st.markdown("### 📋 Revenue par Company × Emplacement × Marque")

agg = ext_data.groupby(
    ["Company", "Location_Code_final", "Marque_NSI", "Posting_Year"], dropna=False
).agg(Revenue_External=("Sales_Amount_Actual", "sum")).reset_index()

if not agg.empty:
    pivot = agg.pivot_table(
        index=["Company", "Location_Code_final", "Marque_NSI"],
        columns="Posting_Year",
        values="Revenue_External",
        aggfunc="sum",
        fill_value=0,
    )
    pivot.columns = [f"Rev {int(y)}" for y in pivot.columns]
    pivot = pivot.reset_index().sort_values(
        pivot.columns[-1] if len(pivot.columns) > 0 else "Company",
        ascending=False,
    )
    display_dataframe(pivot, key="p3_table")

    # ── Chart: Revenue by Location ───────────────────────────────────
    st.markdown("### 📊 Revenue par Emplacement")
    loc_agg = ext_data.groupby(["Location_Code_final", "Company"]).agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index()

    fig = bar_chart(loc_agg, x="Location_Code_final", y="Revenue", color="Company",
                    title="Revenue External par Emplacement et Société", height=500)
    st.plotly_chart(fig, use_container_width=True)

    # ── Pie: Location share ──────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        loc_total = ext_data.groupby("Location_Code_final").agg(
            Revenue=("Sales_Amount_Actual", "sum")
        ).reset_index()
        fig_pie = pie_chart(loc_total, names="Location_Code_final", values="Revenue",
                            title="Répartition par Emplacement")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        company_total = ext_data.groupby("Company").agg(
            Revenue=("Sales_Amount_Actual", "sum")
        ).reset_index()
        fig_pie2 = pie_chart(company_total, names="Company", values="Revenue",
                             title="Répartition par Société")
        st.plotly_chart(fig_pie2, use_container_width=True)

    # ── Chart: Top brands per location ───────────────────────────────
    st.markdown("### 🏷️ Top Marques par Emplacement")
    brand_loc = ext_data.groupby(["Location_Code_final", "Marque_NSI"]).agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index()
    top_brands = brand_loc.groupby("Marque_NSI")["Revenue"].sum().nlargest(15).index
    brand_loc_top = brand_loc[brand_loc["Marque_NSI"].isin(top_brands)]

    fig3 = bar_chart(brand_loc_top, x="Marque_NSI", y="Revenue", color="Location_Code_final",
                     title="Top 15 Marques par Emplacement", barmode="stack", height=500)
    fig3.update_xaxes(tickangle=-45)
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("Pas de données agrégées disponibles.")
