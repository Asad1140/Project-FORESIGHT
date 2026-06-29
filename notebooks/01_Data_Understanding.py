# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Step 1 - Data Understanding
----------------------------------------------
This script performs initial exploratory data analysis on the four core datasets
to profile data quality, sizes, schema, and relations.
"""

import os
import sys
import pandas as pd

# Force standard output to use UTF-8 encoding on Windows to prevent UnicodeEncodeErrors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def main():
    print("==================================================")
    print("Project FORESIGHT: Step 1 - Data Understanding")
    print("==================================================")

    # ----------------------------------------------------
    # Step 1.4: Import Libraries & Locate Data
    # ----------------------------------------------------
    # Determine the correct relative path to the data folder
    if os.path.exists("data"):
        data_dir = "data"
    elif os.path.exists("../data"):
        data_dir = "../data"
    else:
        # Fallback to absolute/relative workspace paths if needed
        data_dir = "Project-FORESIGHT/data"
        
    sales_path = os.path.join(data_dir, "sales_daily.csv")
    inventory_path = os.path.join(data_dir, "inventory_snapshots.csv")
    calendar_path = os.path.join(data_dir, "calendar.csv")
    sku_path = os.path.join(data_dir, "sku_master.csv")

    # ----------------------------------------------------
    # Step 1.5: Read Every CSV
    # ----------------------------------------------------
    print(f"\n[Step 1.5] Reading CSV files from: {data_dir}")
    try:
        sales = pd.read_csv(sales_path)
        inventory = pd.read_csv(inventory_path)
        calendar = pd.read_csv(calendar_path)
        sku = pd.read_csv(sku_path)
        print("Congratulations!\nData loaded successfully.")
    except Exception as e:
        print(f"[ERROR] Error loading datasets: {e}")
        return

    # ----------------------------------------------------
    # Step 1.6: Print First Five Rows & What they Represent
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.6] Printing First 5 Rows of Each Dataset")
    print("="*50)

    print("\n--- SALES DAILY (First 5 Rows) ---")
    print(sales.head())
    print("\n[NOTE] Row Representation (sales_daily):")
    print("   Each row represents daily units sold, revenue generated, unit price,")
    print("   and promotion status for a specific SKU on a specific date.")

    print("\n--- INVENTORY SNAPSHOTS (First 5 Rows) ---")
    print(inventory.head())
    print("\n[NOTE] Row Representation (inventory_snapshots):")
    print("   Each row represents a weekly snapshot of inventory status (on-hand, on-order,")
    print("   lead time, and reorder point) for a specific SKU on a specific snapshot date.")

    print("\n--- CALENDAR (First 5 Rows) ---")
    print(calendar.head())
    print("\n[NOTE] Row Representation (calendar):")
    print("   Each row represents date metadata including week number, month number,")
    print("   season, holiday status, and whether a promotional event was running.")

    print("\n--- SKU MASTER (First 5 Rows) ---")
    print(sku.head())
    print("\n[NOTE] Row Representation (sku_master):")
    print("   Each row represents a unique SKU's metadata, including its category,")
    print("   subcategory, launch date, unit manufacturing cost, and list price.")

    # ----------------------------------------------------
    # Step 1.7: Check Dataset Size
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.7] Check Dataset Size (Shape)")
    print("="*50)
    
    datasets = {
        "Sales Daily": sales,
        "Inventory Snapshots": inventory,
        "Calendar": calendar,
        "SKU Master": sku
    }
    
    for name, df in datasets.items():
        print(f"{name:<20}: {df.shape[0]} rows, {df.shape[1]} columns")

    # ----------------------------------------------------
    # Step 1.8: Check Column Names and Meanings
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.8] Column Meanings & Schema")
    print("="*50)

    print("\n1. sales_daily Columns:")
    print(f"   {list(sales.columns)}")
    print("   - date       : Selling date (YYYY-MM-DD)")
    print("   - sku_id     : Product identifier (FK to sku_master)")
    print("   - units_sold : Number of units sold on this date (Target variable)")
    print("   - revenue    : Total sales value generated on this date (units_sold * unit_price)")
    print("   - unit_price : Price per unit charged on this date")
    print("   - promo_flag : Binary flag (1 if promotion active, 0 otherwise)")

    print("\n2. inventory_snapshots Columns:")
    print(f"   {list(inventory.columns)}")
    print("   - date           : Snapshot date (usually Sunday/weekly)")
    print("   - sku_id         : Product identifier (FK to sku_master)")
    print("   - on_hand_units  : Quantity currently in stock at the warehouse")
    print("   - on_order_units : Quantity currently ordered but not yet received")
    print("   - lead_time_days : Supplier lead time in days to fulfill replenishment")
    print("   - reorder_point  : Stock level threshold below which order is triggered")

    print("\n3. calendar Columns:")
    print(f"   {list(calendar.columns)}")
    print("   - date        : Date (YYYY-MM-DD) (Primary key)")
    print("   - week        : Week of the year (1-53)")
    print("   - month       : Month of the year (1-12)")
    print("   - season      : Season name (Winter, Spring, Summer, Monsoon, Autumn)")
    print("   - is_holiday  : Binary flag (1 if national holiday, 0 otherwise)")
    print("   - promo_event : Name of the promotional event if any (NaN if none)")

    print("\n4. sku_master Columns:")
    print(f"   {list(sku.columns)}")
    print("   - sku_id      : Unique product identifier (Primary key)")
    print("   - category    : Broad product category")
    print("   - subcategory : Specific product subcategory")
    print("   - launch_date : Date the product was introduced")
    print("   - unit_cost   : Cost to manufacture/procure a single unit")
    print("   - list_price  : Manufacturer suggested retail price")

    # ----------------------------------------------------
    # Step 1.9: Check Data Types
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.9] Check Data Types & Info")
    print("="*50)
    
    for name, df in datasets.items():
        print(f"\n--- {name} Info ---")
        df.info()
        
    print("\n[NOTE] Data Type Questions & Reflections:")
    print("   - Is date really a date? No, 'date' is loaded as a string (object) in sales_daily,")
    print("     inventory_snapshots, calendar, and sku_master (launch_date). We must convert")
    print("     these columns to datetime objects later.")
    print("   - Is price numeric? Yes, 'unit_price' (sales_daily), 'unit_cost', and 'list_price'")
    print("     (sku_master) are float64 numeric types.")
    print("   - Is revenue numeric? Yes, 'revenue' (sales_daily) is float64 numeric.")
    print("   - Are units sold numeric? Yes, but 'units_sold' is float64. Since units are discrete")
    print("     counts, it might represent fractional sells (e.g. decimals) or contains nulls.")
    print("     We should cast it to integer after handling missing values.")

    # ----------------------------------------------------
    # Step 1.10: Check Missing Values
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.10] Check Missing Values")
    print("="*50)
    
    for name, df in datasets.items():
        missing = df.isnull().sum()
        print(f"\n--- {name} Missing Count ---")
        print(missing[missing > 0] if missing.sum() > 0 else "No missing values.")
        
    print("\n[NOTE] Missing Value Observations:")
    print("   - sales_daily has 716 missing values in both 'units_sold' and 'revenue'.")
    print("     These are likely aligned (same rows) and represent missing sales data.")
    print("   - calendar has 713 missing values in 'promo_event', which is normal since")
    print("     promotional events are sparse (only 18 days out of 731 have a promo).")
    print("   - inventory_snapshots and sku_master have no missing values.")

    # ----------------------------------------------------
    # Step 1.11: Check Duplicate Rows
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.11] Check Duplicate Rows")
    print("="*50)
    
    for name, df in datasets.items():
        dups = df.duplicated().sum()
        print(f"{name:<20}: {dups} duplicate records found.")
        
    print("\n[NOTE] Duplicate Observations:")
    print("   - sales_daily contains 182 duplicate rows. These duplicate records need")
    print("     to be removed during data cleaning to avoid double-counting sales.")
    print("   - All other datasets have 0 duplicate rows, ensuring relational integrity.")

    # ----------------------------------------------------
    # Step 1.12: Check Statistics
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.12] Descriptive Statistics")
    print("="*50)
    
    for name, df in datasets.items():
        print(f"\n--- {name} Descriptive Statistics ---")
        print(df.describe(include='all'))

    # ----------------------------------------------------
    # Step 1.13: Understand Relationships
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.13] Understand Relationships")
    print("="*50)
    print("""
    The datasets link together through SKU identifiers and Dates:

    sales_daily (Transaction level: SKU + Date)
    |
    |-- sku_id ---> sku_master (Static attributes per SKU)
    |
    +-- date   ---> calendar   (Time metadata per Date)

    inventory_snapshots (Weekly status: SKU + Date)
    |
    |-- sku_id ---> sku_master
    |
    +-- date   ---> calendar
    
    Relationship Summary:
    - sales_daily and sku_master have a many-to-one relationship on `sku_id`.
    - sales_daily and calendar have a many-to-one relationship on `date`.
    - inventory_snapshots and sku_master have a many-to-one relationship on `sku_id`.
    - inventory_snapshots and calendar have a many-to-one relationship on `date`.
    - inventory_snapshots captures weekly snapshots of stock, while sales_daily captures
      daily transactions of demand.
    """)

    # ----------------------------------------------------
    # Step 1.14: Create a Data Dictionary
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.14] Data Dictionary Summary")
    print("="*50)
    print(f"{'Dataset':<22} | {'Purpose':<50}")
    print("-"*75)
    print(f"{'sales_daily':<22} | {'Daily product transactional sales, prices, & promotions'}")
    print(f"{'inventory_snapshots':<22} | {'Weekly snapshots of warehouse inventory levels & lead times'}")
    print(f"{'calendar':<22} | {'Calendar date dimensions, week numbers, holidays & seasons'}")
    print(f"{'sku_master':<22} | {'Master record of SKU classifications, costs, & list prices'}")

    # ----------------------------------------------------
    # Step 1.15: Write Observations
    # ----------------------------------------------------
    print("\n" + "="*50)
    print("[Step 1.15] Executive Summary & Observations")
    print("="*50)
    print("""
    * Total Datasets Analyzed: 4
    * Sales dataset contains daily transactions spanning 200 SKUs.
    * Inventory contains weekly snapshot stock levels (on_hand, on_order) for the same 200 SKUs.
    * Calendar contains holiday and seasonal event information for mapping sales trends.
    * SKU Master contains product detail information including costs and MSRP.
    
    Data Quality Issues Identified:
    1. Missing Values:
       - sales_daily: 716 rows have missing 'units_sold' and 'revenue' values.
       - calendar: 713 missing 'promo_event' values (non-promo days).
    2. Duplicate Rows:
       - sales_daily: 182 duplicate rows need deduplication.
    3. Data Type Conversions Needed:
       - All 'date' columns (sales_daily.date, inventory_snapshots.date, calendar.date, 
         sku_master.launch_date) are loaded as string objects and must be converted to datetime.
       - 'units_sold' in sales_daily is float64 and contains missing values. Once clean, 
         we can convert this to integer.
    4. Dataset Merging:
       - The datasets are easily linkable via 'sku_id' and 'date' keys.
    """)
    print("==================================================")

if __name__ == "__main__":
    main()
