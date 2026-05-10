"""
DAX measures reimplemented in Python/Pandas.
All 17 measures from the Power Pivot model.
"""
import pandas as pd
import numpy as np


def _external_mask(df: pd.DataFrame) -> pd.Series:
    """Mask for external (non-interco) rows with actual sales."""
    has_sales = df["Sales_Amount_Actual"] != 0
    not_interco = ~df["IsInterco_computed"].fillna(False).astype(bool)
    return has_sales & not_interco


# ═══════════════════════════════════════════════════════════════════════
#  PRIMARY MEASURES
# ═══════════════════════════════════════════════════════════════════════

def revenue_external(df: pd.DataFrame) -> float:
    """Revenue External = SUM(Sales_Amount_Actual) WHERE external."""
    mask = _external_mask(df)
    return df.loc[mask, "Sales_Amount_Actual"].sum()


def cogs_external(df: pd.DataFrame) -> float:
    """COGS External = -SUM(Cost_Amount_Actual) WHERE external sales rows."""
    mask = _external_mask(df)
    return -df.loc[mask, "Cost_Amount_Actual"].sum()


def gross_margin_external(df: pd.DataFrame) -> float:
    """Gross Margin External = Revenue - COGS."""
    return revenue_external(df) - cogs_external(df)


def margin_pct_external(df: pd.DataFrame) -> float:
    """Margin % External = Gross Margin / Revenue."""
    rev = revenue_external(df)
    return gross_margin_external(df) / rev if rev != 0 else 0.0


def qty_sold_external(df: pd.DataFrame) -> float:
    """Qty Sold External = -SUM(Invoiced_Quantity) WHERE external."""
    mask = _external_mask(df)
    return -df.loc[mask, "Invoiced_Quantity"].sum()


def actual_selling_price(df: pd.DataFrame) -> float:
    """Average selling price = Revenue / Qty."""
    qty = qty_sold_external(df)
    return revenue_external(df) / qty if qty != 0 else 0.0


def avg_cost_per_unit(df: pd.DataFrame) -> float:
    """Average cost per unit = COGS / Qty."""
    qty = qty_sold_external(df)
    return cogs_external(df) / qty if qty != 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════
#  DERIVED MEASURES
# ═══════════════════════════════════════════════════════════════════════

def actual_unit_margin(df: pd.DataFrame) -> float:
    return actual_selling_price(df) - avg_cost_per_unit(df)


def actual_margin_pct(df: pd.DataFrame) -> float:
    asp = actual_selling_price(df)
    return actual_unit_margin(df) / asp if asp != 0 else 0.0


def revenue_total(df: pd.DataFrame) -> float:
    """Revenue total (including interco)."""
    return df["Sales_Amount_Actual"].sum()


def cost_amount_actual_external(df: pd.DataFrame) -> float:
    mask = _external_mask(df)
    return df.loc[mask, "Cost_Amount_Actual"].sum()


def actual_purchase_price(df: pd.DataFrame) -> float:
    qty = qty_sold_external(df)
    return cost_amount_actual_external(df) / qty if qty != 0 else 0.0


def inbound_qty(df: pd.DataFrame) -> float:
    """Sum of Valued_Quantity for inbound entries."""
    if "Item_Ledger_Entry_Type" in df.columns:
        mask = df["Item_Ledger_Entry_Type"].isin(["Purchase", "Positive Adjmt."])
        return df.loc[mask, "Valued_Quantity"].sum()
    return df["Valued_Quantity"].sum()


def inbound_cost(df: pd.DataFrame) -> float:
    if "Item_Ledger_Entry_Type" in df.columns:
        mask = df["Item_Ledger_Entry_Type"].isin(["Purchase", "Positive Adjmt."])
        return df.loc[mask, "Cost_Amount_Actual"].sum()
    return df["Cost_Amount_Actual"].sum()


def actual_cost_per_unit(df: pd.DataFrame) -> float:
    qty = inbound_qty(df)
    return inbound_cost(df) / qty if qty != 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════
#  GROUPED AGGREGATION HELPER
# ═══════════════════════════════════════════════════════════════════════

def compute_measures_grouped(
    df: pd.DataFrame,
    group_cols: list[str],
    measures: list[str] | None = None,
) -> pd.DataFrame:
    """
    Compute selected measures grouped by given columns.
    Returns a DataFrame with group columns + measure columns.
    """
    if measures is None:
        measures = ["Revenue External", "COGS External", "Gross Margin External", "Margin % External", "Qty Sold External"]

    # Pre-filter: only rows with non-zero sales and external
    mask = _external_mask(df)
    ext_df = df[mask].copy()

    # Aggregate
    agg_dict = {}
    if "Revenue External" in measures:
        agg_dict["Revenue External"] = ("Sales_Amount_Actual", "sum")
    if "COGS External" in measures:
        agg_dict["COGS External"] = ("Cost_Amount_Actual", lambda x: -x.sum())
    if "Qty Sold External" in measures:
        agg_dict["Qty Sold External"] = ("Invoiced_Quantity", lambda x: -x.sum())

    if not agg_dict:
        return pd.DataFrame()

    # Build groupby
    valid_cols = [c for c in group_cols if c in ext_df.columns]
    if not valid_cols:
        return pd.DataFrame()

    result = ext_df.groupby(valid_cols, dropna=False).agg(
        **{k: v for k, v in agg_dict.items()}
    ).reset_index()

    # Derived
    if "Gross Margin External" in measures and "Revenue External" in result.columns and "COGS External" in result.columns:
        result["Gross Margin External"] = result["Revenue External"] - result["COGS External"]
    if "Margin % External" in measures and "Revenue External" in result.columns and "Gross Margin External" in result.columns:
        result["Margin % External"] = np.where(
            result["Revenue External"] != 0,
            result["Gross Margin External"] / result["Revenue External"],
            0,
        )

    return result


def compute_pivot_table(
    df: pd.DataFrame,
    index_cols: list[str],
    column_col: str,
    value_col: str = "Sales_Amount_Actual",
    aggfunc: str = "sum",
    external_only: bool = True,
) -> pd.DataFrame:
    """Create a pivot table like a TCD, optionally filtering to external only."""
    work_df = df.copy()
    if external_only:
        mask = _external_mask(work_df)
        work_df = work_df[mask]

    valid_idx = [c for c in index_cols if c in work_df.columns]
    if not valid_idx or column_col not in work_df.columns or value_col not in work_df.columns:
        return pd.DataFrame()

    pivot = pd.pivot_table(
        work_df,
        index=valid_idx,
        columns=column_col,
        values=value_col,
        aggfunc=aggfunc,
        fill_value=0,
    )
    return pivot.reset_index()
