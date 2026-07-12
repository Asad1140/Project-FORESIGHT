# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Data Preparation & Advanced Cleaning Module
--------------------------------------------------------------
Handles loading, validation, outlier capping, consistency checks,
and audit logging for the sales, sku, calendar, and inventory datasets.
"""

import os
import json
import logging
from typing import Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def clean_and_validate_data(data_dir: str = "data") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Ingests raw datasets, validates their schema and types, performs cleaning operations,
    saves cleaned versions, and outputs a pipeline run log.

    Args:
        data_dir (str): Directory where raw data is stored and clean data will be saved.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            Cleaned DataFrames for SKU master, sales, calendar, and inventory snapshots.
    """
    logger.info("Initializing Data Preparation Pipeline...")

    # Define file paths
    sales_path = os.path.join(data_dir, "sales_daily.csv")
    inventory_path = os.path.join(data_dir, "inventory_snapshots.csv")
    calendar_path = os.path.join(data_dir, "calendar.csv")
    sku_path = os.path.join(data_dir, "sku_master.csv")

    # Load raw data
    for path in [sales_path, inventory_path, calendar_path, sku_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required input file not found: {path}")

    sales_raw = pd.read_csv(sales_path)
    inventory_raw = pd.read_csv(inventory_path)
    calendar_raw = pd.read_csv(calendar_path)
    sku_raw = pd.read_csv(sku_path)

    # Initialize log
    log = {
        "raw_sales_rows": len(sales_raw),
        "clean_sales_rows": 0,
        "duplicate_sales_removed": 0,
        "missing_sales_removed": 0,
        "invalid_skus_removed": 0,
        "negative_values_removed": 0,
        "revenue_consistency_corrected": 0,
        "outliers_capped": 0,
        "pipeline_status": "SUCCESS"
    }

    # Make working copies
    sales = sales_raw.copy()
    inventory = inventory_raw.copy()
    calendar = calendar_raw.copy()
    sku = sku_raw.copy()

    # --- Convert dates first to ensure we can do temporal validations ---
    sales["date"] = pd.to_datetime(sales["date"])
    inventory["date"] = pd.to_datetime(inventory["date"])
    calendar["date"] = pd.to_datetime(calendar["date"])
    sku["launch_date"] = pd.to_datetime(sku["launch_date"])

    # --- Clean SKU Master ---
    sku = sku.drop_duplicates(subset=["sku_id"])
    sku = sku.dropna(subset=["sku_id"])
    sku["unit_cost"] = pd.to_numeric(sku["unit_cost"], errors="coerce")
    sku["list_price"] = pd.to_numeric(sku["list_price"], errors="coerce")
    # Handle negative cost/price by replacing with absolute values
    sku["unit_cost"] = sku["unit_cost"].abs()
    sku["list_price"] = sku["list_price"].abs()

    # --- Clean Calendar ---
    calendar = calendar.drop_duplicates(subset=["date"])
    calendar = calendar.dropna(subset=["date"])
    calendar["week"] = pd.to_numeric(calendar["week"], errors="coerce")
    calendar["month"] = pd.to_numeric(calendar["month"], errors="coerce")
    calendar["is_holiday"] = pd.to_numeric(calendar["is_holiday"], errors="coerce").fillna(0).astype(int)

    # --- Clean Sales ---
    # 1. Deduplicate
    initial_sales_rows = len(sales)
    sales = sales.drop_duplicates()
    log["duplicate_sales_removed"] = initial_sales_rows - len(sales)

    # 2. Missing Value Removal
    # Drop rows where critical columns (sku_id, date, units_sold, revenue) are missing
    pre_missing_rows = len(sales)
    sales = sales.dropna(subset=["sku_id", "date", "units_sold", "revenue"])
    log["missing_sales_removed"] = pre_missing_rows - len(sales)

    # Convert numeric fields and handle incorrect dtypes
    sales["units_sold"] = pd.to_numeric(sales["units_sold"], errors="coerce")
    sales["revenue"] = pd.to_numeric(sales["revenue"], errors="coerce")
    sales["unit_price"] = pd.to_numeric(sales["unit_price"], errors="coerce")
    sales["promo_flag"] = pd.to_numeric(sales["promo_flag"], errors="coerce").fillna(0).astype(int)

    # Drop any rows that became null after coercion
    sales = sales.dropna(subset=["units_sold", "revenue", "unit_price"])

    # 3. Negative Value Check
    # Remove rows where units_sold, revenue, or unit_price are negative
    pre_neg_rows = len(sales)
    sales = sales[(sales["units_sold"] >= 0) & (sales["revenue"] >= 0) & (sales["unit_price"] >= 0)]
    log["negative_values_removed"] = pre_neg_rows - len(sales)

    # 4. Invalid SKU Verification (Foreign Key check)
    pre_invalid_sku_rows = len(sales)
    valid_sku_ids = set(sku["sku_id"].unique())
    sales = sales[sales["sku_id"].isin(valid_sku_ids)]
    log["invalid_skus_removed"] = pre_invalid_sku_rows - len(sales)

    # 5. Revenue Consistency Validation
    # Revenue should equal units_sold * unit_price. Adjust if outside a threshold.
    expected_revenue = sales["units_sold"] * sales["unit_price"]
    revenue_mismatch = np.abs(sales["revenue"] - expected_revenue) > (0.01 * expected_revenue + 1.0)
    log["revenue_consistency_corrected"] = int(revenue_mismatch.sum())
    sales.loc[revenue_mismatch, "revenue"] = expected_revenue[revenue_mismatch]

    # 6. Outlier Detection & Capping (IQR-based per SKU)
    # Using 3 * IQR to identify and cap extreme values in units_sold
    sales["outlier_flag"] = False
    for sku_id in sales["sku_id"].unique():
        sku_mask = sales["sku_id"] == sku_id
        sku_sales = sales.loc[sku_mask, "units_sold"]
        if len(sku_sales) > 4:
            q1 = sku_sales.quantile(0.25)
            q3 = sku_sales.quantile(0.75)
            iqr = q3 - q1
            upper_bound = q3 + 3.0 * iqr
            
            # Identify outliers above the upper bound
            outliers = sku_mask & (sales["units_sold"] > upper_bound)
            outlier_count = outliers.sum()
            if outlier_count > 0:
                log["outliers_capped"] += int(outlier_count)
                sales.loc[outliers, "units_sold"] = upper_bound
                # Re-calculate revenue based on capped units
                sales.loc[outliers, "revenue"] = upper_bound * sales.loc[outliers, "unit_price"]
                sales.loc[outliers, "outlier_flag"] = True

    log["clean_sales_rows"] = len(sales)

    # --- Clean Inventory ---
    inventory = inventory.drop_duplicates()
    inventory = inventory.dropna(subset=["sku_id", "date"])
    # Filter foreign key relationship
    inventory = inventory[inventory["sku_id"].isin(valid_sku_ids)]
    
    # Coerce inventory numerical columns
    inventory["on_hand_units"] = pd.to_numeric(inventory["on_hand_units"], errors="coerce").fillna(0).clip(lower=0)
    inventory["on_order_units"] = pd.to_numeric(inventory["on_order_units"], errors="coerce").fillna(0).clip(lower=0)
    inventory["lead_time_days"] = pd.to_numeric(inventory["lead_time_days"], errors="coerce").fillna(14).clip(lower=1).astype(int)
    inventory["reorder_point"] = pd.to_numeric(inventory["reorder_point"], errors="coerce").fillna(10).clip(lower=0).astype(int)

    # --- Save Cleaned Datasets ---
    sales.to_csv(os.path.join(data_dir, "clean_sales.csv"), index=False)
    inventory.to_csv(os.path.join(data_dir, "clean_inventory.csv"), index=False)
    calendar.to_csv(os.path.join(data_dir, "clean_calendar.csv"), index=False)
    sku.to_csv(os.path.join(data_dir, "clean_sku_master.csv"), index=False)

    # --- Save Pipeline Run Log ---
    log_dir = os.path.join(data_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "pipeline_run_log.json")
    
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4)

    # Save a copy directly under project root for deliverables checklist
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_log_path = os.path.join(project_root, "pipeline_run_log.json")
    with open(root_log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4)

    # Save a copy directly under project root's logs directory (expected by updated config.py)
    root_logs_dir = os.path.join(project_root, "logs")
    os.makedirs(root_logs_dir, exist_ok=True)
    root_logs_path = os.path.join(root_logs_dir, "pipeline_run_log.json")
    with open(root_logs_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4)

    logger.info(f"Pipeline executed successfully. Cleaned files and run log saved to {data_dir}")
    logger.info(f"Cleaned Sales rows: {log['clean_sales_rows']} (Dropped {log['raw_sales_rows'] - log['clean_sales_rows']})")
    
    return sku, sales, calendar, inventory


if __name__ == "__main__":
    # Locate data directory relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_data_dir = os.path.join(project_root, "data")
    if not os.path.exists(target_data_dir):
        target_data_dir = "data"
    clean_and_validate_data(target_data_dir)
