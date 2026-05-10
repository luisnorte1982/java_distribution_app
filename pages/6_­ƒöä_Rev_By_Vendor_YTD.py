"""
Page 6 — Revenue by Vendor Name YTD
Suivi YTD par fournisseur avec comparaison N-1 / N.
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.measures import _external_mask
from utils.ui_helpers import sidebar_filters, bar_chart, line_chart, display_dataframe, kpi_row

st.set_page_config(page_title="Rev by Vendor YTD", page_icon="🔄", layout="wide")

st.title("🔄 Revenue par Fournisseur — YTD")
st.markdown("*Suivi YTD par fournisseur — comparaison glissante par mois entre N-1 et N*")

if "enriched_df" not in st.session_state:
    st.warning("⚠️ Veuillez d'abord charger les données depuis la page d'accueil.")
    st.stop()

df = st.session_state["enriched_df"]
filtered = sidebar_filters(df, key_prefix="p6", show_distribution=False)

if filtered.empty:
    st.info("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

mask_ext = _external_mask(filtered)
ext_data = filtered[mask_ext].copy()

# ── KPIs ─────────────────────────────────────────────────────────────
total_rev = ext_data["Sales_Amount_Actual"].sum()
n_vendors = ext_data["Vendor_Name"].nunique()

years = sorted(ext_data["Posting_Year"].dropna().unique())
delta = None
if len(years) >= 2:
    rev_prev = ext_data.loc[ext_data["Posting_Year"] == years[-2], "Sales_Amount_Actual"].sum()
    rev_curr = ext_data.loc[ext_data["Posting_Year"] == years[-1], "Sales_Amount_Actual"].sum()
    delta = (rev_curr - rev_prev) / abs(rev_prev) if rev_prev != 0 else None

kpi_row([
    ("Revenue External Total", total_rev, "currency"),
    ("Nb Fournisseurs", n_vendors, "qty"),
    ("Croissance N/N-1", delta if delta else 0, "pct"),
])

st.divider()

# ── Table: Vendor × Month × Year ────────────────────────────────────
st.markdown("### 📋 Revenue YTD par Fournisseur × Mois × Année")

month_names = {1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Jun",
               7: "Jul", 8: "Aoû", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc"}

monthly = ext_data.groupby(
    ["Vendor_Name", "Posting_Month", "Posting_Year"], dropna=False
).agg(Revenue_External=("Sales_Amount_Actual", "sum")).reset_index()

if not monthly.empty:
    # Create pivot with multi-level columns: Month × Year
    monthly["Col_Label"] = (
        monthly["Posting_Month"].map(month_names) + " " + monthly["Posting_Year"].astype(int).astype(str)
    )

    pivot = monthly.pivot_table(
        index="Vendor_Name",
        columns=["Posting_Month", "Posting_Year"],
        values="Revenue_External",
        aggfunc="sum",
        fill_value=0,
    )

    # Flatten columns
    new_cols = []
    for month, year in pivot.columns:
        label = f"{month_names.get(int(month), str(month))} {int(year)}"
        new_cols.append(label)
    pivot.columns = new_cols

    # Sort columns by chronological order
    def sort_key(col):
        parts = col.rsplit(" ", 1)
        if len(parts) == 2:
            m_name, yr = parts
            m_num = {v: k for k, v in month_names.items()}.get(m_name, 0)
            return (int(yr), m_num)
        return (0, 0)

    sorted_cols = sorted(pivot.columns, key=sort_key)
    pivot = pivot[sorted_cols]

    # Add YTD totals per year
    for year in years:
        yr = int(year)
        year_cols = [c for c in pivot.columns if c.endswith(str(yr))]
        if year_cols:
            pivot[f"YTD {yr}"] = pivot[year_cols].sum(axis=1)

    pivot = pivot.reset_index()

    # Add delta between YTD columns
    ytd_cols = [c for c in pivot.columns if c.startswith("YTD")]
    if len(ytd_cols) >= 2:
        prev_ytd = ytd_cols[-2]
        curr_ytd = ytd_cols[-1]
        pivot["Δ YTD"] = pivot[curr_ytd] - pivot[prev_ytd]
        pivot["Δ %"] = np.where(pivot[prev_ytd] != 0, pivot["Δ YTD"] / abs(pivot[prev_ytd]), 0)

    # Sort by latest YTD
    sort_col = ytd_cols[-1] if ytd_cols else "Vendor_Name"
    pivot = pivot.sort_values(sort_col, ascending=False)

    display_dataframe(pivot, key="p6_table", height=600)

    # ── Chart: Top 20 Vendors YTD ────────────────────────────────────
    st.markdown("### 📊 Top 20 Fournisseurs — Revenue YTD")
    vendor_total = ext_data.groupby(["Vendor_Name", "Posting_Year"]).agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index()

    top_vendors = vendor_total.groupby("Vendor_Name")["Revenue"].sum().nlargest(20).index
    chart_data = vendor_total[vendor_total["Vendor_Name"].isin(top_vendors)]
    chart_data["Année"] = chart_data["Posting_Year"].astype(int).astype(str)

    fig = bar_chart(chart_data, x="Vendor_Name", y="Revenue", color="Année",
                    title="Top 20 Fournisseurs — Revenue par Année", height=550)
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # ── Monthly trend for top vendors ────────────────────────────────
    st.markdown("### 📉 Évolution mensuelle — Top 10 Fournisseurs")
    top10 = vendor_total.groupby("Vendor_Name")["Revenue"].sum().nlargest(10).index
    trend_data = ext_data[ext_data["Vendor_Name"].isin(top10)].groupby(
        ["Vendor_Name", "Posting_Month"]
    ).agg(Revenue=("Sales_Amount_Actual", "sum")).reset_index()
    trend_data["Mois"] = trend_data["Posting_Month"].map(month_names)
    trend_data = trend_data.sort_values("Posting_Month")

    fig2 = line_chart(trend_data, x="Mois", y="Revenue", color="Vendor_Name",
                      title="Évolution mensuelle — Top 10 Fournisseurs", height=500)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Pas de données fournisseurs disponibles.")
