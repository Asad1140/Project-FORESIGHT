# Data Quality and Profiling Report

This report outlines the structural details, data quality issues, and cleaning strategies for the datasets provided in **Project FORESIGHT**.

## 📊 Dataset Overview

The data operates on a star-schema architecture composed of four main files:

| File Name | Primary Key / Grain | Key Columns | Purpose |
| :--- | :--- | :--- | :--- |
| `sku_master.csv` | `sku_id` | `category`, `subcategory`, `unit_cost`, `list_price` | Product dimension |
| `calendar.csv` | `date` | `week`, `month`, `season`, `is_holiday`, `promo_event` | Calendar dimension |
| `sales_daily.csv` | `date` + `sku_id` | `units_sold`, `revenue`, `unit_price`, `promo_flag` | Sales transactional fact table |
| `inventory_snapshots.csv` | `date` + `sku_id` | `on_hand_units`, `on_order_units`, `lead_time_days` | Inventory snapshot fact table |

---

## 🔍 Identified Data Quality Issues

In accordance with the client's data maturity, the raw exports contain several issues that must be cleaned:

### 1. Inconsistent Category Casing (`sku_master.csv`)
*   **Issue**: Categories such as `Furnishings` are occasionally written as lowercase `furnishings` or with trailing spaces `Furnishings `.
*   **Impact**: Grouping or aggregating sales by category would create separate, duplicate groups, leading to incorrect category-level insights.

### 2. Missing Values (`sales_daily.csv`)
*   **Issue**: Approximately 0.8% of rows in `sales_daily.csv` have missing values (`NaN`) in both the `units_sold` and `revenue` fields.
*   **Impact**: These rows will cause errors in aggregations or feature engineering if left untreated.

### 3. Duplicate Rows (`sales_daily.csv`)
*   **Issue**: Around 0.2% of the sales records are duplicated.
*   **Impact**: Double-counting sales inflates revenue metrics and distorts model forecasting weights.

---

## 🛠️ Data Cleaning Plan

The preprocessing pipeline in `pipeline.py` will implement the following steps:

1.  **Standardize SKU Master Categories**:
    *   Apply `.strip().title()` to the `category` and `subcategory` columns.
2.  **Deduplicate Sales Records**:
    *   Identify and remove exact duplicate rows from `sales_daily.csv`.
3.  **Impute Missing Sales Data**:
    *   Filter out or fill missing `units_sold` and `revenue` with 0 if no transactions occurred, or drop rows where the transaction is entirely unrecoverable.
4.  **Enforce Schema Integrity**:
    *   Cast columns to their correct datatypes (e.g., date strings to datetime objects, flags to integers).
