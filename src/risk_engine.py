# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Inventory Risk & Decision Scoring Engine
----------------------------------------------------------
Implements calculations for stockout risk, overstock risk, quadrant classifications,
safety stock, and financial impacts (sales-at-risk, capital-locked).
"""

from datetime import timedelta
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def calculate_risk_scoring(
    latest_inventory: pd.DataFrame,
    sku_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    safety_stock_weeks: float,
    lt_override: bool = False,
    lt_days: int = 14,
    selected_category: str = "All"
) -> pd.DataFrame:
    """
    Calculates stockout and overstock risk metrics, classifies SKUs into decision quadrants,
    and quantifies financial impacts.

    Args:
        latest_inventory (pd.DataFrame): Current snapshot of SKU inventories.
        sku_df (pd.DataFrame): SKU properties (prices, cost, category).
        sales_df (pd.DataFrame): Daily historical sales transactions.
        safety_stock_weeks (float): User configurable safety stock buffer in weeks.
        lt_override (bool): If True, replaces real lead times with simulation value.
        lt_days (int): Simulation lead time value in days.
        selected_category (str): Product category to filter by ("All" or specific name).

    Returns:
        pd.DataFrame: Computed risk analysis DataFrame.
    """
    logger.info("Running risk scoring engine...")
    
    # Join inventory snapshots with product master
    df = pd.merge(latest_inventory, sku_df, on="sku_id")
    
    # Filter by category if selected
    if selected_category != "All":
        df = df[df["category"] == selected_category].copy()
        
    if df.empty:
        logger.warning(f"No records found for category: {selected_category}")
        return df

    # Find the end of historical sales data
    sales_end = sales_df["date"].max()
    
    # 1. 12-week average sales rate
    sales_start_12w = sales_end - timedelta(weeks=12)
    recent_sales_12w = sales_df[(sales_df["date"] >= sales_start_12w) & (sales_df["date"] <= sales_end)]
    weekly_sales_12w = recent_sales_12w.groupby("sku_id")["units_sold"].sum() / 12.0
    weekly_sales_12w = weekly_sales_12w.reindex(df["sku_id"], fill_value=0.1)
    
    # 2. 4-week average sales rate (for trend momentum)
    sales_start_4w = sales_end - timedelta(weeks=4)
    recent_sales_4w = sales_df[(sales_df["date"] >= sales_start_4w) & (sales_df["date"] <= sales_end)]
    weekly_sales_4w = recent_sales_4w.groupby("sku_id")["units_sold"].sum() / 4.0
    weekly_sales_4w = weekly_sales_4w.reindex(df["sku_id"], fill_value=0.1)
    
    # Trend multiplier (demand momentum)
    sales_trend = weekly_sales_4w / (weekly_sales_12w + 1e-5)
    
    df["weekly_avg_sales"] = df["sku_id"].map(weekly_sales_12w)
    df["sales_trend_multiplier"] = df["sku_id"].map(sales_trend)
    
    # Overwrite lead times if override is active
    if lt_override:
        df["lead_time_days"] = lt_days
        
    # Lead time demand = average daily demand * lead time days
    df["lead_time_demand"] = df["weekly_avg_sales"] * (df["lead_time_days"] / 7.0)
    
    # Safety stock = safety stock weeks * weekly average sales
    df["safety_stock"] = df["weekly_avg_sales"] * safety_stock_weeks
    
    # Reorder point = lead time demand + safety stock
    df["reorder_point_calc"] = df["lead_time_demand"] + df["safety_stock"]
    
    # Current supply = inventory on hand + on order units
    df["current_supply"] = df["on_hand_units"] + df["on_order_units"]
    
    # --- Multi-Factor Risk Calculations ---
    # Factor A: Stock ratio deficit
    df["stock_deficit_factor"] = (1.0 - (df["current_supply"] / (df["reorder_point_calc"] + 1e-5))).clip(0.0, 1.0)
    
    # Factor B: Lead time exposure
    df["lead_time_exposure"] = (df["lead_time_days"] / 21.0).clip(0.0, 1.0)
    
    # Factor C: Demand acceleration momentum
    df["trend_exposure"] = ((df["sales_trend_multiplier"] - 1.0) * 0.3).clip(0.0, 0.4)
    
    # Factor D: Promotion sensitivity exposure by category
    promo_sensitivity = df["category"].map({
        "Small Appliances": 0.25,
        "Furnishings": 0.2,
        "Home Decor": 0.15,
        "Kitchenware": 0.1
    }).fillna(0.05)
    df["promo_exposure"] = promo_sensitivity
    
    # Weighted Stockout Risk Score
    df["stockout_risk"] = (
        0.55 * df["stock_deficit_factor"] +
        0.15 * df["lead_time_exposure"] +
        0.15 * df["trend_exposure"] +
        0.15 * df["promo_exposure"]
    ).clip(0.0, 1.0)
    
    # Overstock Risk: compare on_hand against 16 weeks of demand supply
    df["overstock_limit"] = df["weekly_avg_sales"] * 8.0
    df["overstock_risk"] = df["on_hand_units"] / (df["weekly_avg_sales"] * 16.0 + 1e-5)
    df["overstock_risk"] = df["overstock_risk"].clip(0.0, 1.0)
    
    # Classify into quadrants
    conditions = [
        (df["stockout_risk"] > 0.55) & (df["overstock_risk"] < 0.45),  # Reorder Now
        (df["overstock_risk"] > 0.55) & (df["stockout_risk"] < 0.45),  # Markdown / Clear
        (df["stockout_risk"] > 0.55) & (df["overstock_risk"] > 0.45),  # Watch / Volatile
    ]
    choices = ["REORDER NOW", "MARKDOWN / CLEAR", "WATCH / VOLATILE"]
    df["quadrant"] = np.select(conditions, choices, default="HEALTHY")
    
    # Financial Impact Calculations
    df["units_short"] = np.maximum(0.0, df["reorder_point_calc"] - df["current_supply"])
    df["sales_at_risk"] = df["units_short"] * df["list_price"]
    
    df["excess_units"] = np.maximum(0.0, df["on_hand_units"] - (df["weekly_avg_sales"] * 6.0))
    df["capital_locked"] = df["excess_units"] * df["unit_cost"]
    
    logger.info("Risk engine calculations completed.")
    return df
