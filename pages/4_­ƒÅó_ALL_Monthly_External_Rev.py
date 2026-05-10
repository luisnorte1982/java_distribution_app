"""
Page 4 — ALL Monthly External Revenue
Revenue mensuel TOUTES activités par société et location.
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.measures import _external_mask
from utils.ui_helpers import sidebar_filters, bar_chart, line_chart, display_dataframe, kpi_row

st.set_page_config(page_title="ALL Monthly External Rev", page_icon="🏢", layout="wide")

st.title("🏢 ALL Monthly External Revenue")
st.markdown("*Revenue mensuel **toutes activités** par société et emplacement — comparaison N-1 / N*")

if "enriched_df" not in st.session_state:
    st.warning("⚠️ Veuillez d'abord charger les données depuis la page d'accueil.")
    st.stop()

df = st.session_state["enriched_df"]

# No distribution filter on this page
filtered = sidebar_filters(df, key_prefix="p4", show_distribution=False)

if filtered.empty:
    st.info("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

mask_ext = _external_mask(filtered)
ext_data = filtered[mask_ext].copy()

# ── KPIs ─────────────────────────────────────────────────────────────
total_rev = ext_data["Sales_Amount_Actual"].sum()
total_gm = total_rev - (-ext_data["Cost_Amount_Actual"].sum())

years = sorted(ext_data["Posting_Year"].dropna().unique())
delta_rev = None
if len(years) >= 2:
    rev_prev = ext_data.loc[ext_data["Posting_Year"] == years[-2], "Sales_Amount_Actual"].sum()
    rev_curr = ext_data.loc[ext_data["Posting_Year"] == years[-1], "Sales_Amount_Actual"].sum()
    delta_rev = (rev_curr - rev_prev) / abs(rev_prev) if rev_prev != 0 else None

kpi_row([
    ("Revenue External Total", total_rev, "currency"),
    ("Marge Brute", total_gm, "currency"),
    ("Nb Sociétés", ext_data["Company"].nunique(), "qty"),
    ("Nb Emplacements", ext_data["Location_Code_final"].nunique(), "qty"),
])

st.divider()

# ── Table: Company × Location × Year ────────────────────────────────
st.markdown("### 📋 Revenue par Société × Emplacement")
agg = ext_data.groupby(
    ["Company", "Location_Code_final", "Posting_Year"], dropna=False
).agg(Revenue_External=("Sales_Amount_Actual", "sum")).reset_index()

if not agg.empty:
    pivot = agg.pivot_table(
        index=["Company", "Location_Code_final"],
        columns="Posting_Year",
        values="Revenue_External",
        aggfunc="sum",
        fill_value=0,
    )
    pivot.columns = [f"Rev {int(y)}" for y in pivot.columns]
    pivot = pivot.reset_index()

    # Add delta
    rev_cols_sorted = sorted([c for c in pivot.columns if c.startswith("Rev ")])
    if len(rev_cols_sorted) >= 2:
        prev_col = rev_cols_sorted[-2]
        curr_col = rev_cols_sorted[-1]
        pivot["Δ Rev"] = pivot[curr_col] - pivot[prev_col]
        pivot["Δ %"] = np.where(pivot[prev_col] != 0, pivot["Δ Rev"] / abs(pivot[prev_col]), 0)

    # Subtotals per company
    pivot_with_totals = pivot.copy()
    for company in pivot_with_totals["Company"].unique():
        mask = pivot_with_totals["Company"] == company
        subtotal = pivot_with_totals[mask].select_dtypes(include=[np.number]).sum()
        subtotal_row = {"Company": company, "Location_Code_final": "** TOTAL **"}
        for col in subtotal.index:
            subtotal_row[col] = subtotal[col]
        if "Δ %" in subtotal_row:
            rev_prev_val = subtotal_row.get(rev_cols_sorted[-2], 0) if len(rev_cols_sorted) >= 2 else 0
            subtotal_row["Δ %"] = subtotal_row.get("Δ Rev", 0) / abs(rev_prev_val) if rev_prev_val else 0
        pivot_with_totals = pd.concat([pivot_with_totals, pd.DataFrame([subtotal_row])], ignore_index=True)

    display_dataframe(pivot_with_totals, key="p4_table")

    # ── Chart: Monthly trend ─────────────────────────────────────────
    st.markdown("### 📉 Évolution mensuelle")
    month_names = {1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Jun",
                   7: "Jul", 8: "Aoû", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc"}
    monthly = ext_data.groupby(["Posting_Month", "Posting_Year"]).agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index()
    monthly["Mois"] = monthly["Posting_Month"].map(month_names)
    monthly["Année"] = monthly["Posting_Year"].astype(str)
    monthly = monthly.sort_values("Posting_Month")

    fig = bar_chart(monthly, x="Mois", y="Revenue", color="Année",
                    title="Revenue External mensuel — Comparaison par année", height=500)
    st.plotly_chart(fig, use_container_width=True)

    # ── Chart: Company comparison ────────────────────────────────────
    st.markdown("### 🏢 Comparaison par Société")
    company_monthly = ext_data.groupby(["Posting_Month", "Company"]).agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index()
    company_monthly["Mois"] = company_monthly["Posting_Month"].map(month_names)
    company_monthly = company_monthly.sort_values("Posting_Month")

    fig2 = line_chart(company_monthly, x="Mois", y="Revenue", color="Company",
                      title="Revenue mensuel par Société")
    st.plotly_chart(fig2, use_container_width=True)

    # ── Chart: Location breakdown ────────────────────────────────────
    st.markdown("### 📍 Revenue par Emplacement")
    loc_agg = ext_data.groupby("Location_Code_final").agg(
        Revenue=("Sales_Amount_Actual", "sum")
    ).reset_index().sort_values("Revenue", ascending=False)

    fig3 = bar_chart(loc_agg, x="Location_Code_final", y="Revenue",
                     title="Revenue External par Emplacement", height=450)
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("Pas de données agrégées disponibles.")
