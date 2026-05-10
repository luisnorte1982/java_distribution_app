"""
Page 1 — DIS Monthly External Revenue
Revenue mensuel Distribution par fournisseur et marque, comparaison N-1/N.
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.measures import compute_measures_grouped, _external_mask
from utils.ui_helpers import sidebar_filters, bar_chart, display_dataframe, kpi_row

st.set_page_config(page_title="DIS Monthly External Rev", page_icon="📊", layout="wide")

st.title("📊 DIS Monthly External Revenue")
st.markdown("*Revenue mensuel de l'activité **DISTRIBUTION** par fournisseur et marque — comparaison N-1 / N*")

# ── Load data from session ───────────────────────────────────────────
if "enriched_df" not in st.session_state:
    st.warning("⚠️ Veuillez d'abord charger les données depuis la page d'accueil.")
    st.stop()

df = st.session_state["enriched_df"]

# ── Filters ──────────────────────────────────────────────────────────
filtered = sidebar_filters(df, key_prefix="p1", show_distribution=True)

if filtered.empty:
    st.info("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────
mask_ext = _external_mask(filtered)
total_rev = filtered.loc[mask_ext, "Sales_Amount_Actual"].sum()
total_cogs = -filtered.loc[mask_ext, "Cost_Amount_Actual"].sum()
total_gm = total_rev - total_cogs
margin_pct = total_gm / total_rev if total_rev != 0 else 0

kpi_row([
    ("Revenue External", total_rev, "currency"),
    ("COGS External", total_cogs, "currency"),
    ("Marge Brute External", total_gm, "currency"),
    ("Marge %", margin_pct, "pct"),
])

st.divider()

# ── Pivot: Company × Vendor × Brand × Year → Revenue + GM ────────────
pivot_data = filtered[mask_ext].copy()
group_cols = ["Company", "Vendor_Name", "Marque_NSI", "Posting_Year"]
agg = pivot_data.groupby(group_cols, dropna=False).agg(
    Revenue_External=("Sales_Amount_Actual", "sum"),
    Cost_Amount=("Cost_Amount_Actual", "sum"),
).reset_index()
agg["Gross_Margin_External"] = agg["Revenue_External"] - (-agg["Cost_Amount"])
agg.drop(columns=["Cost_Amount"], inplace=True)

# Pivot years as columns
if not agg.empty:
    years = sorted(agg["Posting_Year"].dropna().unique())

    # Revenue pivot
    rev_pivot = agg.pivot_table(
        index=["Company", "Vendor_Name", "Marque_NSI"],
        columns="Posting_Year",
        values="Revenue_External",
        aggfunc="sum",
        fill_value=0,
    )
    rev_pivot.columns = [f"Rev {int(y)}" for y in rev_pivot.columns]

    # GM pivot
    gm_pivot = agg.pivot_table(
        index=["Company", "Vendor_Name", "Marque_NSI"],
        columns="Posting_Year",
        values="Gross_Margin_External",
        aggfunc="sum",
        fill_value=0,
    )
    gm_pivot.columns = [f"GM {int(y)}" for y in gm_pivot.columns]

    result = pd.concat([rev_pivot, gm_pivot], axis=1).reset_index()

    # Add delta columns if 2 years
    if len(years) >= 2:
        y1, y2 = int(years[-2]), int(years[-1])
        if f"Rev {y1}" in result.columns and f"Rev {y2}" in result.columns:
            result[f"Δ Rev {y2}/{y1}"] = result[f"Rev {y2}"] - result[f"Rev {y1}"]
            result[f"Δ Rev %"] = np.where(
                result[f"Rev {y1}"] != 0,
                (result[f"Rev {y2}"] - result[f"Rev {y1}"]) / abs(result[f"Rev {y1}"]),
                0,
            )

    # Sort
    rev_cols = [c for c in result.columns if c.startswith("Rev ")]
    if rev_cols:
        result = result.sort_values(rev_cols[-1], ascending=False)

    # ── Display table ────────────────────────────────────────────────
    st.markdown("### 📋 Tableau détaillé")
    display_dataframe(result, key="p1_table")

    # ── Chart: Top 15 vendors by revenue ─────────────────────────────
    st.markdown("### 📈 Top 15 Fournisseurs")
    vendor_agg = agg.groupby(["Vendor_Name", "Posting_Year"], dropna=False).agg(
        Revenue_External=("Revenue_External", "sum"),
    ).reset_index()

    top_vendors = (
        vendor_agg.groupby("Vendor_Name")["Revenue_External"]
        .sum().nlargest(15).index
    )
    chart_data = vendor_agg[vendor_agg["Vendor_Name"].isin(top_vendors)]
    chart_data["Posting_Year"] = chart_data["Posting_Year"].astype(str)

    fig = bar_chart(
        chart_data, x="Vendor_Name", y="Revenue_External", color="Posting_Year",
        title="Revenue External — Top 15 Fournisseurs",
        height=550,
    )
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # ── Chart: Revenue by Brand ──────────────────────────────────────
    st.markdown("### 🏷️ Revenue par Marque")
    brand_agg = agg.groupby(["Marque_NSI", "Posting_Year"], dropna=False).agg(
        Revenue_External=("Revenue_External", "sum"),
    ).reset_index()
    top_brands = brand_agg.groupby("Marque_NSI")["Revenue_External"].sum().nlargest(20).index
    brand_chart = brand_agg[brand_agg["Marque_NSI"].isin(top_brands)]
    brand_chart["Posting_Year"] = brand_chart["Posting_Year"].astype(str)

    fig2 = bar_chart(
        brand_chart, x="Marque_NSI", y="Revenue_External", color="Posting_Year",
        title="Revenue External — Top 20 Marques",
        height=500,
    )
    fig2.update_xaxes(tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Pas de données agrégées disponibles.")
