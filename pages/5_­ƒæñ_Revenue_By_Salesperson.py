"""
Page 5 — Revenue by Salesperson
Revenue + Marge brute détaillés par client et article (granularité fine).
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.measures import _external_mask
from utils.ui_helpers import sidebar_filters, bar_chart, display_dataframe, kpi_row

st.set_page_config(page_title="Revenue by Salesperson", page_icon="👤", layout="wide")

st.title("👤 Revenue par Vendeur / Client / Article")
st.markdown("*Revenue + Marge brute détaillés par client et article — granularité la plus fine*")

if "enriched_df" not in st.session_state:
    st.warning("⚠️ Veuillez d'abord charger les données depuis la page d'accueil.")
    st.stop()

df = st.session_state["enriched_df"]
filtered = sidebar_filters(df, key_prefix="p5", show_distribution=True)

if filtered.empty:
    st.info("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

mask_ext = _external_mask(filtered)
ext_data = filtered[mask_ext].copy()

# ── KPIs ─────────────────────────────────────────────────────────────
total_rev = ext_data["Sales_Amount_Actual"].sum()
total_gm = total_rev - (-ext_data["Cost_Amount_Actual"].sum())
margin_pct = total_gm / total_rev if total_rev != 0 else 0

kpi_row([
    ("Revenue External", total_rev, "currency"),
    ("Marge Brute", total_gm, "currency"),
    ("Marge %", margin_pct, "pct"),
    ("Nb Articles", ext_data["Description"].nunique() if "Description" in ext_data.columns else 0, "qty"),
])

st.divider()

# ── Salesperson selector ─────────────────────────────────────────────
if "Salesperson_Code" in ext_data.columns:
    salespersons = sorted(ext_data["Salesperson_Code"].dropna().unique())
    if salespersons:
        sel_sp = st.multiselect("🔎 Filtrer par Vendeur", salespersons, key="p5_salesperson")
        if sel_sp:
            ext_data = ext_data[ext_data["Salesperson_Code"].isin(sel_sp)]

# ── Monthly pivot by Client × Article ────────────────────────────────
st.markdown("### 📋 Détail par Client × Article")

month_names = {1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Jun",
               7: "Jul", 8: "Aoû", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc"}

# Revenue
group_cols = ["Sell_to_Customer_Name", "Description", "Posting_Month"]
if "Description" not in ext_data.columns:
    group_cols = ["Sell_to_Customer_Name", "Item_No", "Posting_Month"]

monthly = ext_data.groupby(group_cols, dropna=False).agg(
    Revenue_External=("Sales_Amount_Actual", "sum"),
    Cost_Amount=("Cost_Amount_Actual", "sum"),
).reset_index()
monthly["GM_External"] = monthly["Revenue_External"] - (-monthly["Cost_Amount"])

if not monthly.empty:
    index_cols = group_cols[:2]  # Customer + Article

    # Revenue pivot
    rev_pivot = monthly.pivot_table(
        index=index_cols,
        columns="Posting_Month",
        values="Revenue_External",
        aggfunc="sum",
        fill_value=0,
    )
    rev_pivot.columns = [f"Rev {month_names.get(int(c), str(c))}" for c in rev_pivot.columns]

    # GM pivot
    gm_pivot = monthly.pivot_table(
        index=index_cols,
        columns="Posting_Month",
        values="GM_External",
        aggfunc="sum",
        fill_value=0,
    )
    gm_pivot.columns = [f"GM {month_names.get(int(c), str(c))}" for c in gm_pivot.columns]

    result = pd.concat([rev_pivot, gm_pivot], axis=1).reset_index()
    result["Total Rev"] = result[[c for c in result.columns if c.startswith("Rev ")]].sum(axis=1)
    result["Total GM"] = result[[c for c in result.columns if c.startswith("GM ")]].sum(axis=1)
    result["Margin %"] = np.where(result["Total Rev"] != 0, result["Total GM"] / result["Total Rev"], 0)
    result = result.sort_values("Total Rev", ascending=False)

    # Limit display
    max_rows = st.slider("Nombre de lignes", 50, min(2000, len(result)), 200, key="p5_rows")
    display_dataframe(result.head(max_rows), key="p5_table", height=600)

    # ── Chart: Top Customers ─────────────────────────────────────────
    st.markdown("### 📊 Top 20 Clients")
    cust_total = ext_data.groupby("Sell_to_Customer_Name").agg(
        Revenue=("Sales_Amount_Actual", "sum"),
        Cost=("Cost_Amount_Actual", "sum"),
    ).reset_index()
    cust_total["GM"] = cust_total["Revenue"] - (-cust_total["Cost"])
    cust_total = cust_total.nlargest(20, "Revenue")

    fig = bar_chart(cust_total, x="Sell_to_Customer_Name", y="Revenue",
                    title="Top 20 Clients — Revenue External", height=500)
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # ── Chart: Top Articles ──────────────────────────────────────────
    st.markdown("### 📦 Top 20 Articles")
    desc_col = "Description" if "Description" in ext_data.columns else "Item_No"
    art_total = ext_data.groupby(desc_col).agg(
        Revenue=("Sales_Amount_Actual", "sum"),
    ).reset_index().nlargest(20, "Revenue")

    fig2 = bar_chart(art_total, x=desc_col, y="Revenue",
                     title="Top 20 Articles — Revenue External", height=500)
    fig2.update_xaxes(tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)

    # ── Salesperson performance ──────────────────────────────────────
    if "Salesperson_Code" in ext_data.columns:
        st.markdown("### 🏆 Performance par Vendeur")
        sp_total = ext_data.groupby("Salesperson_Code").agg(
            Revenue=("Sales_Amount_Actual", "sum"),
            Cost=("Cost_Amount_Actual", "sum"),
            Nb_Clients=("Sell_to_Customer_Name", "nunique"),
        ).reset_index()
        sp_total["GM"] = sp_total["Revenue"] - (-sp_total["Cost"])
        sp_total["Margin %"] = np.where(sp_total["Revenue"] != 0, sp_total["GM"] / sp_total["Revenue"], 0)
        sp_total = sp_total.sort_values("Revenue", ascending=False)

        display_dataframe(sp_total, key="p5_sp_table")

else:
    st.info("Pas de données détaillées disponibles.")
