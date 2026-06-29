import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Create folders if they do not exist
os.makedirs("Project-FORESIGHT/data", exist_ok=True)

print("Starting synthetic data generation...")

# 1. Generate SKU Master
print("Generating sku_master.csv...")
num_skus = 200
categories = {
    "Furnishings": ["Bedding", "Cushions", "Rugs"],
    "Décor": ["Lighting", "Wall Art", "Vases"],
    "Small Appliances": ["Kitchenware", "Coffee Makers", "Blenders"]
}

sku_data = []
for i in range(1, num_skus + 1):
    sku_id = f"SKU_{i:03d}"
    cat = np.random.choice(list(categories.keys()))
    subcat = np.random.choice(categories[cat])
    
    # Introduce deliberate casing/space inconsistencies
    raw_cat = cat
    r = np.random.random()
    if r < 0.05:
        raw_cat = cat.lower()
    elif r < 0.10:
        raw_cat = cat + " "
        
    unit_cost = round(float(np.random.uniform(150, 4500)), 2)
    markup = np.random.uniform(1.4, 2.2)
    list_price = round(unit_cost * markup, 2)
    
    launch_days_offset = np.random.randint(0, 365)
    launch_date = (datetime(2023, 1, 1) + timedelta(days=launch_days_offset)).strftime("%Y-%m-%d")
    
    sku_data.append({
        "sku_id": sku_id,
        "category": raw_cat,
        "subcategory": subcat,
        "launch_date": launch_date,
        "unit_cost": unit_cost,
        "list_price": list_price
    })

sku_df = pd.DataFrame(sku_data)
sku_df.to_csv("Project-FORESIGHT/data/sku_master.csv", index=False)


# 2. Generate Calendar Dimension
print("Generating calendar.csv...")
start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 12, 31)
date_range = pd.date_range(start_date, end_date)

calendar_data = []
for dt in date_range:
    date_str = dt.strftime("%Y-%m-%d")
    week = dt.isocalendar()[1]
    month = dt.month
    
    if month in [12, 1, 2]:
        season = "Winter"
    elif month in [3, 4, 5]:
        season = "Spring"
    elif month in [6, 7, 8]:
        season = "Summer"
    else:
        season = "Autumn"
        
    is_holiday = 0
    promo_event = "None"
    
    if dt.month == 1 and dt.day == 26:
        is_holiday = 1
    elif dt.month == 8 and dt.day == 15:
        is_holiday = 1
        promo_event = "Independence Day Special"
    elif dt.month == 12 and dt.day == 25:
        is_holiday = 1
        promo_event = "Christmas Sale"
    elif dt.month == 1 and dt.day == 1:
        is_holiday = 1
        promo_event = "New Year Bash"
    elif dt.month == 3 and dt.day in [15, 16]:
        is_holiday = 1
        promo_event = "Holi Fest"
    elif dt.month == 11 and dt.day in [1, 2, 3]:
        is_holiday = 1
        promo_event = "Diwali Bumper Sale"
    elif dt.month == 11 and dt.day >= 23 and dt.weekday() == 4:
        promo_event = "Black Friday"
        
    calendar_data.append({
        "date": date_str,
        "week": week,
        "month": month,
        "season": season,
        "is_holiday": is_holiday,
        "promo_event": promo_event
    })

calendar_df = pd.DataFrame(calendar_data)
calendar_df.to_csv("Project-FORESIGHT/data/calendar.csv", index=False)


# 3. Generate Sales Daily (Fact Table)
print("Generating sales_daily.csv...")
clean_sku_df = sku_df.copy()
clean_sku_df["category"] = clean_sku_df["category"].str.strip().str.title()

# Convert calendar to dictionary for O(1) lookups
calendar_dict = calendar_df.set_index("date").to_dict(orient="index")

sales_records = []
for sku_idx, row in clean_sku_df.iterrows():
    sku_id = row["sku_id"]
    list_price = row["list_price"]
    sku_base_demand = np.random.choice([0.1, 0.5, 1.5, 3.5, 8.0], p=[0.15, 0.45, 0.25, 0.10, 0.05])
    launch_dt = datetime.strptime(row["launch_date"], "%Y-%m-%d")
    
    for dt in date_range:
        if dt < launch_dt:
            continue
            
        date_str = dt.strftime("%Y-%m-%d")
        cal_row = calendar_dict[date_str]
        
        lam = sku_base_demand
        
        # Day of week effect
        day_of_week = dt.weekday()
        if day_of_week == 4: # Friday
            lam *= 1.2
        elif day_of_week in [5, 6]: # Sat, Sun
            lam *= 1.5
            
        # Monthly effect
        if dt.month in [10, 11, 12]:
            lam *= 1.3
            
        # Promotions
        promo_flag = 0
        current_price = list_price
        
        if cal_row["promo_event"] != "None":
            promo_flag = 1
            lam *= 1.8
            discount = np.random.uniform(0.1, 0.25)
            current_price = round(list_price * (1 - discount), 2)
        elif np.random.random() < 0.08:
            promo_flag = 1
            lam *= 1.5
            discount = np.random.uniform(0.05, 0.15)
            current_price = round(list_price * (1 - discount), 2)
            
        units_sold = np.random.poisson(lam)
        
        if units_sold > 0:
            revenue = round(units_sold * current_price, 2)
            sales_records.append({
                "date": date_str,
                "sku_id": sku_id,
                "units_sold": units_sold,
                "revenue": revenue,
                "unit_price": current_price,
                "promo_flag": promo_flag
            })
            
sales_df = pd.DataFrame(sales_records)

# Introduce quality issues
missing_mask = np.random.random(len(sales_df)) < 0.008
sales_df.loc[missing_mask, "units_sold"] = np.nan
sales_df.loc[missing_mask, "revenue"] = np.nan

duplicates = sales_df.sample(frac=0.002, replace=True)
sales_df = pd.concat([sales_df, duplicates], ignore_index=True)

sales_df = sales_df.sort_values(by=["date", "sku_id"]).reset_index(drop=True)
sales_df.to_csv("Project-FORESIGHT/data/sales_daily.csv", index=False)


# 4. Generate Inventory Snapshots
print("Generating inventory_snapshots.csv...")
snapshot_dates = calendar_df[pd.to_datetime(calendar_df["date"]).dt.weekday == 6]["date"].tolist()

# Group sales to a dictionary of (sku_id, date) -> units_sold for fast lookups
sales_grouped = sales_df.dropna(subset=["units_sold"]).groupby(["sku_id", "date"])["units_sold"].sum().to_dict()

inventory_records = []
for sku_idx, row in clean_sku_df.iterrows():
    sku_id = row["sku_id"]
    sku_base_demand = np.random.choice([0.1, 0.5, 1.5, 3.5, 8.0], p=[0.15, 0.45, 0.25, 0.10, 0.05])
    weekly_avg_sales = sku_base_demand * 7
    
    lead_time_days = int(np.random.choice([7, 14, 21], p=[0.3, 0.5, 0.2]))
    safety_stock = int(weekly_avg_sales * 1.5)
    reorder_point = int((weekly_avg_sales * (lead_time_days / 7)) + safety_stock)
    reorder_point = max(5, reorder_point)
    
    order_quantity = int(weekly_avg_sales * 4)
    order_quantity = max(10, order_quantity)
    
    on_hand = int(weekly_avg_sales * 5)
    on_order = 0
    eta = None
    
    for snapshot_date in snapshot_dates:
        dt = datetime.strptime(snapshot_date, "%Y-%m-%d")
        
        if eta is not None and dt >= eta:
            on_hand += on_order
            on_order = 0
            eta = None
            
        # Calculate weekly sales using fast dictionary lookup
        actual_weekly_sales = 0
        for offset in range(7):
            day = dt + timedelta(days=offset)
            actual_weekly_sales += sales_grouped.get((sku_id, day.strftime("%Y-%m-%d")), 0)
            
        on_hand = max(0, on_hand - int(actual_weekly_sales))
        
        if (on_hand + on_order) <= reorder_point:
            on_order = order_quantity
            eta = dt + timedelta(days=lead_time_days)
            
        inventory_records.append({
            "date": snapshot_date,
            "sku_id": sku_id,
            "on_hand_units": on_hand,
            "on_order_units": on_order,
            "lead_time_days": lead_time_days,
            "reorder_point": reorder_point
        })
        
inventory_df = pd.DataFrame(inventory_records)
inventory_df.to_csv("Project-FORESIGHT/data/inventory_snapshots.csv", index=False)

print("\nData generation complete!")
print(f"sku_master.csv: {sku_df.shape}")
print(f"calendar.csv: {calendar_df.shape}")
print(f"sales_daily.csv: {sales_df.shape}")
print(f"inventory_snapshots.csv: {inventory_df.shape}")
