"""
Shared UI components: filters, KPI cards, chart builders, export buttons.
"""
import io
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from config.settings import COLORS, CURRENCY_FORMAT, PCT_FORMAT


# ═══════════════════════════════════════════════════════════════════════
#  KPI CARDS
# ═══════════════════════════════════════════════════════════════════════

def kpi_card(label: str, value: float, fmt: str = "currency", delta: float | None = None, delta_fmt: str = "pct"):
    """Render a KPI metric with optional delta."""
    if fmt == "currency":
        display = f"{value:,.0f} €"
    elif fmt == "pct":
        display = f"{value:.1%}"
    elif fmt == "qty":
        display = f"{value:,.0f}"
    else:
        display = f"{value:,.2f}"

    delta_str = None
    delta_color = "normal"
    if delta is not None:
        if delta_fmt == "pct":
            delta_str = f"{delta:+.1%}"
        else:
            delta_str = f"{delta:+,.0f} €"
        delta_color = "normal"

    st.metric(label=label, value=display, delta=delta_str, delta_color=delta_color)


def kpi_row(metrics: list[tuple]):
    """Display multiple KPI cards in columns.
    metrics: list of (label, value, fmt, delta, delta_fmt) tuples.
    """
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            label = m[0]
            value = m[1]
            fmt = m[2] if len(m) > 2 else "currency"
            delta = m[3] if len(m) > 3 else None
            delta_fmt = m[4] if len(m) > 4 else "pct"
            kpi_card(label, value, fmt, delta, delta_fmt)


# ═══════════════════════════════════════════════════════════════════════
#  SIDEBAR FILTERS
# ═══════════════════════════════════════════════════════════════════════

def sidebar_filters(df: pd.DataFrame, key_prefix: str = "", show_distribution: bool = True) -> pd.DataFrame:
    """Standard sidebar filters. Returns filtered DataFrame."""
    filtered = df.copy()

    with st.sidebar:
        st.markdown("### 🔍 Filtres")

        # ── Year ─────────────────────────────────────────────────────
        if "Posting_Year" in filtered.columns:
            years = sorted(filtered["Posting_Year"].dropna().unique())
            sel_years = st.multiselect("Année", years, default=years, key=f"{key_prefix}_year")
            if sel_years:
                filtered = filtered[filtered["Posting_Year"].isin(sel_years)]

        # ── Month ────────────────────────────────────────────────────
        if "Posting_Month" in filtered.columns:
            months = sorted(filtered["Posting_Month"].dropna().unique())
            month_names = {
                1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
                5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
                9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
            }
            month_options = {f"{m} - {month_names.get(int(m), '')}": m for m in months}
            sel_months = st.multiselect(
                "Mois", list(month_options.keys()), default=list(month_options.keys()),
                key=f"{key_prefix}_month",
            )
            if sel_months:
                sel_month_vals = [month_options[m] for m in sel_months]
                filtered = filtered[filtered["Posting_Month"].isin(sel_month_vals)]

        # ── Company ──────────────────────────────────────────────────
        if "Company" in filtered.columns:
            companies = sorted(filtered["Company"].dropna().unique())
            sel_companies = st.multiselect("Société", companies, default=companies, key=f"{key_prefix}_company")
            if sel_companies:
                filtered = filtered[filtered["Company"].isin(sel_companies)]

        # ── Distribution filter ──────────────────────────────────────
        if show_distribution and "Dimension_Value_Code" in filtered.columns:
            dist_only = st.checkbox("Distribution uniquement", value=True, key=f"{key_prefix}_dist")
            if dist_only:
                filtered = filtered[filtered["Dimension_Value_Code"] == "DISTRIBUTION"]

        # ── Vendor ───────────────────────────────────────────────────
        if "Vendor_Name" in filtered.columns:
            vendors = sorted(filtered["Vendor_Name"].dropna().unique())
            if vendors:
                sel_vendors = st.multiselect("Fournisseur", vendors, key=f"{key_prefix}_vendor")
                if sel_vendors:
                    filtered = filtered[filtered["Vendor_Name"].isin(sel_vendors)]

        # ── Brand ────────────────────────────────────────────────────
        if "Marque_NSI" in filtered.columns:
            brands = sorted(filtered["Marque_NSI"].dropna().unique())
            if brands:
                sel_brands = st.multiselect("Marque", brands, key=f"{key_prefix}_brand")
                if sel_brands:
                    filtered = filtered[filtered["Marque_NSI"].isin(sel_brands)]

        # ── Customer ─────────────────────────────────────────────────
        if "Sell_to_Customer_Name" in filtered.columns:
            customers = sorted(filtered["Sell_to_Customer_Name"].dropna().unique())
            if customers:
                sel_custs = st.multiselect("Client", customers, key=f"{key_prefix}_cust")
                if sel_custs:
                    filtered = filtered[filtered["Sell_to_Customer_Name"].isin(sel_custs)]

        # ── Location ─────────────────────────────────────────────────
        if "Location_Code_final" in filtered.columns:
            locs = sorted(filtered["Location_Code_final"].dropna().unique())
            if locs:
                sel_locs = st.multiselect("Emplacement", locs, key=f"{key_prefix}_loc")
                if sel_locs:
                    filtered = filtered[filtered["Location_Code_final"].isin(sel_locs)]

    return filtered


# ═══════════════════════════════════════════════════════════════════════
#  CHARTS
# ═══════════════════════════════════════════════════════════════════════

def bar_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None,
              title: str = "", barmode: str = "group", orientation: str = "v",
              text_auto: bool = True, height: int = 500) -> go.Figure:
    """Standard bar chart."""
    fig = px.bar(
        df, x=x, y=y, color=color, title=title,
        barmode=barmode, orientation=orientation,
        text_auto=".2s" if text_auto else False,
        color_discrete_sequence=COLORS["chart_palette"],
        height=height,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


def line_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None,
               title: str = "", height: int = 450) -> go.Figure:
    fig = px.line(
        df, x=x, y=y, color=color, title=title, markers=True,
        color_discrete_sequence=COLORS["chart_palette"],
        height=height,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str = "",
              height: int = 400, hole: float = 0.4) -> go.Figure:
    fig = px.pie(
        df, names=names, values=values, title=title, hole=hole,
        color_discrete_sequence=COLORS["chart_palette"],
        height=height,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        font=dict(family="Segoe UI, sans-serif"),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def waterfall_chart(labels: list, values: list, title: str = "", height: int = 400) -> go.Figure:
    fig = go.Figure(go.Waterfall(
        name="",
        orientation="v",
        measure=["relative"] * (len(values) - 1) + ["total"],
        x=labels,
        y=values,
        connector={"line": {"color": "#aaa"}},
        increasing={"marker": {"color": COLORS["success"]}},
        decreasing={"marker": {"color": COLORS["danger"]}},
        totals={"marker": {"color": COLORS["primary"]}},
    ))
    fig.update_layout(title=title, height=height, showlegend=False)
    return fig


# ═══════════════════════════════════════════════════════════════════════
#  DATA TABLE + EXPORT
# ═══════════════════════════════════════════════════════════════════════

def display_dataframe(df: pd.DataFrame, title: str = "", key: str = "table",
                      show_export: bool = True, height: int = 400):
    """Display a DataFrame with optional export buttons."""
    if title:
        st.markdown(f"#### {title}")

    st.dataframe(df, use_container_width=True, height=height, key=key)

    if show_export and not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
            st.download_button(
                "📥 Export CSV", csv, f"{key}.csv", "text/csv",
                key=f"{key}_csv",
            )
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Data")
            st.download_button(
                "📥 Export Excel", buffer.getvalue(), f"{key}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{key}_xlsx",
            )


def format_currency_col(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Format currency columns for display."""
    display_df = df.copy()
    for col in cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f} €" if pd.notna(x) else "")
    return display_df


def format_pct_col(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Format percentage columns for display."""
    display_df = df.copy()
    for col in cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "")
    return display_df
