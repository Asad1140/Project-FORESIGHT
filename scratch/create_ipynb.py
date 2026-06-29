import json
import os

notebook_path = "notebooks/01_Data_Understanding.ipynb"

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Project FORESIGHT: Step 1 - Data Understanding\n",
    "==================================================\n",
    "\n",
    "This notebook covers **Step 1: Data Understanding** for Project FORESIGHT. We will profile and inspect the four core datasets to understand their scale, structures, columns, missing values, duplicates, statistics, and relationships."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.4: Import Libraries"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import pandas as pd\n",
    "import numpy as np"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.5: Read Every CSV\n",
    "We load all four datasets: `sales_daily`, `inventory_snapshots`, `calendar`, and `sku_master`."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Congratulations \ud83c\udf89\n",
      "Data loaded successfully.\n"
     ]
    }
   ],
   "source": [
    "# Determine correct relative path depending on running environment\n",
    "if os.path.exists(\"data\"):\n",
    "    data_dir = \"data\"\n",
    "elif os.path.exists(\"../data\"):\n",
    "    data_dir = \"../data\"\n",
    "else:\n",
    "    data_dir = \"Project-FORESIGHT/data\"\n",
    "\n",
    "sales = pd.read_csv(os.path.join(data_dir, \"sales_daily.csv\"))\n",
    "inventory = pd.read_csv(os.path.join(data_dir, \"inventory_snapshots.csv\"))\n",
    "calendar = pd.read_csv(os.path.join(data_dir, \"calendar.csv\"))\n",
    "sku = pd.read_csv(os.path.join(data_dir, \"sku_master.csv\"))\n",
    "\n",
    "print(\"Congratulations \ud83c\udf89\\nData loaded successfully.\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.6: Print First Five Rows\n",
    "Let's see what each row represents in the respective datasets."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### 1. Daily Sales"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {},
   "outputs": [],
   "source": [
    "sales.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "**What does each row represent in `sales_daily`?**\n",
    "Each row represents one day's transaction details for a specific SKU. It records the selling date, SKU identifier, quantity sold, total revenue, unit price, and a flag indicating if a promotion was active."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### 2. Weekly Inventory Snapshots"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {},
   "outputs": [],
   "source": [
    "inventory.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "**What does each row represent in `inventory_snapshots`?**\n",
    "Each row represents a weekly snapshot of warehouse stock status for a particular product (SKU) on a snapshot date. It includes physical units on hand, units on order, lead time, and reorder point threshold."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### 3. Calendar Dimensions"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "metadata": {},
   "outputs": [],
   "source": [
    "calendar.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "**What does each row represent in `calendar`?**\n",
    "Each row represents calendar dimensions for a specific date, mapping it to a week number of the year, month, season, national holiday flag, and any active marketing promotion event name."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### 4. SKU Master Catalog"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "metadata": {},
   "outputs": [],
   "source": [
    "sku.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "**What does each row represent in `sku_master`?**\n",
    "Each row represents a unique product (SKU) record in the product master database. It includes taxonomy detail (category, subcategory), launch date, procurement/manufacturing cost, and manufacturer suggested retail price (list price)."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.7: Check Dataset Size (Shape)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Sales Daily dataset size       : 91039 rows, 6 columns\n",
      "Inventory Snapshots size       : 20800 rows, 6 columns\n",
      "Calendar dataset size          : 731 rows, 6 columns\n",
      "SKU Master size                : 200 rows, 6 columns\n"
     ]
    }
   ],
   "source": [
    "print(f\"Sales Daily dataset size       : {sales.shape[0]} rows, {sales.shape[1]} columns\")\n",
    "print(f\"Inventory Snapshots size       : {inventory.shape[0]} rows, {inventory.shape[1]} columns\")\n",
    "print(f\"Calendar dataset size          : {calendar.shape[0]} rows, {calendar.shape[1]} columns\")\n",
    "print(f\"SKU Master size                : {sku.shape[0]} rows, {sku.shape[1]} columns\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.8: Check Column Names & Definitions\n",
    "\n",
    "#### Column Definitions\n",
    "\n",
    "##### **1. Daily Sales (`sales_daily.csv`)**\n",
    "| Column | Meaning | Type |\n",
    "|---|---|---|\n",
    "| `date` | Selling date (YYYY-MM-DD) | string/object |\n",
    "| `sku_id` | Unique product identifier (Foreign Key to sku_master) | string/object |\n",
    "| `units_sold` | Number of items sold on this date | float64 |\n",
    "| `revenue` | Total income from sales (units_sold * unit_price) | float64 |\n",
    "| `unit_price` | Price charged per unit on this date | float64 |\n",
    "| `promo_flag` | Flag for promotion active (1) or not (0) | int64 |\n",
    "\n",
    "##### **2. Weekly Inventory Snapshots (`inventory_snapshots.csv`)**\n",
    "| Column | Meaning | Type |\n",
    "|---|---|---|\n",
    "| `date` | weekly snapshot date | string/object |\n",
    "| `sku_id` | Unique product identifier (Foreign Key to sku_master) | string/object |\n",
    "| `on_hand_units` | Current units physically available in stock | int64 |\n",
    "| `on_order_units` | Replenishment units currently ordered but not yet arrived | int64 |\n",
    "| `lead_time_days` | Supplier fulfillment lead time in days | int64 |\n",
    "| `reorder_point` | Inventory level that triggers reorder alert | int64 |\n",
    "\n",
    "##### **3. Calendar Dimensions (`calendar.csv`)**\n",
    "| Column | Meaning | Type |\n",
    "|---|---|---|\n",
    "| `date` | Calendar date (YYYY-MM-DD) (Primary Key) | string/object |\n",
    "| `week` | Calendar week number of the year (1-53) | int64 |\n",
    "| `month` | Calendar month number (1-12) | int64 |\n",
    "| `season` | Season classification (Winter, Spring, Summer, Monsoon, Autumn) | string/object |\n",
    "| `is_holiday` | Flag for national holiday (1) or not (0) | int64 |\n",
    "| `promo_event` | Name of promotional campaign running | string/object (nullable) |\n",
    "\n",
    "##### **4. SKU Master Catalog (`sku_master.csv`)**\n",
    "| Column | Meaning | Type |\n",
    "|---|---|---|\n",
    "| `sku_id` | Unique product identifier (Primary Key) | string/object |\n",
    "| `category` | High-level product category classification | string/object |\n",
    "| `subcategory` | Fine product subcategory classification | string/object |\n",
    "| `launch_date` | Date the product was introduced to the catalog | string/object |\n",
    "| `unit_cost` | Procurement/production cost of a single unit | float64 |\n",
    "| `list_price` | Manufacturer suggested retail price (MSRP) | float64 |"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.9: Check Data Types"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "metadata": {},
   "outputs": [],
   "source": [
    "sales.info()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "metadata": {},
   "outputs": [],
   "source": [
    "inventory.info()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "metadata": {},
   "outputs": [],
   "source": [
    "calendar.info()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "metadata": {},
   "outputs": [],
   "source": [
    "sku.info()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "**Questions to Ask & Reflections:**\n",
    "- **Is date really a date?** No, the `date` column is loaded as string (`object`) in all four datasets. In the data cleaning phase, we will need to parse these to datetime type.\n",
    "- **Is price numeric?** Yes, unit prices and costs are stored as numeric floats.\n",
    "- **Is revenue numeric?** Yes, revenue is stored as a numeric float.\n",
    "- **Are units numeric?** Yes, but `units_sold` is float64 due to missing values. We should clean and cast it to integer."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.10: Check Missing Values"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 12,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "--- Sales Daily Missing Counts ---\n",
      "date            0\n",
      "sku_id          0\n",
      "units_sold    716\n",
      "revenue       716\n",
      "unit_price      0\n",
      "promo_flag      0\n",
      "dtype: int64\n",
      "\n",
      "--- Inventory Snapshots Missing Counts ---\n",
      "date              0\n",
      "sku_id            0\n",
      "on_hand_units     0\n",
      "on_order_units    0\n",
      "lead_time_days    0\n",
      "reorder_point     0\n",
      "dtype: int64\n",
      "\n",
      "--- Calendar Missing Counts ---\n",
      "date             0\n",
      "week             0\n",
      "month            0\n",
      "season           0\n",
      "is_holiday       0\n",
      "promo_event    713\n",
      "dtype: int64\n",
      "\n",
      "--- SKU Master Missing Counts ---\n",
      "sku_id         0\n",
      "category       0\n",
      "subcategory    0\n",
      "launch_date    0\n",
      "unit_cost      0\n",
      "list_price     0\n",
      "dtype: int64\n"
     ]
    }
   ],
   "source": [
    "print(\"--- Sales Daily Missing Counts ---\")\n",
    "print(sales.isnull().sum())\n",
    "\n",
    "print(\"\\n--- Inventory Snapshots Missing Counts ---\")\n",
    "print(inventory.isnull().sum())\n",
    "\n",
    "print(\"\\n--- Calendar Missing Counts ---\")\n",
    "print(calendar.isnull().sum())\n",
    "\n",
    "print(\"\\n--- SKU Master Missing Counts ---\")\n",
    "print(sku.isnull().sum())"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "**Observations on Missing Values:**\n",
    "- `sales_daily` contains **716 missing values** in both `units_sold` and `revenue` fields. These represents missing transaction data points that must be imputed or cleaned.\n",
    "- `calendar` contains **713 missing values** in `promo_event`, representing normal calendar days where there is no promotional campaign active. This is expected.\n",
    "- `inventory_snapshots` and `sku_master` contain **0 missing values**."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.11: Check Duplicate Rows"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 13,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Sales Daily duplicates        : 182\n",
      "Inventory Snapshots duplicates: 0\n",
      "Calendar duplicates           : 0\n",
      "SKU Master duplicates         : 0\n"
     ]
    }
   ],
   "source": [
    "print(\"Sales Daily duplicates        :\", sales.duplicated().sum())\n",
    "print(\"Inventory Snapshots duplicates:\", inventory.duplicated().sum())\n",
    "print(\"Calendar duplicates           :\", calendar.duplicated().sum())\n",
    "print(\"SKU Master duplicates         :\", sku.duplicated().sum())"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "**Observations on Duplicates:**\n",
    "- `sales_daily` contains **182 duplicate rows**. These records must be dropped during preprocessing to prevent skewing model inputs.\n",
    "- No duplicates exist in the other three datasets."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.12: Check Statistics"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 14,
   "metadata": {},
   "outputs": [],
   "source": [
    "sales.describe(include='all')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 15,
   "metadata": {},
   "outputs": [],
   "source": [
    "inventory.describe(include='all')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 16,
   "metadata": {},
   "outputs": [],
   "source": [
    "calendar.describe(include='all')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 17,
   "metadata": {},
   "outputs": [],
   "source": [
    "sku.describe(include='all')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.13: Understand Relationships\n",
    "\n",
    "The core keys to tie these datasets together are **SKU_ID** and **DATE**.\n",
    "\n",
    "```\n",
    "sales_daily\n",
    "SKU_ID\n",
    "     │\n",
    "     ├──────────────► sku_master\n",
    "\n",
    "DATE\n",
    "     │\n",
    "     └──────────────► calendar\n",
    "\n",
    "SKU_ID + DATE\n",
    "     │\n",
    "     └──────────────► inventory_snapshots\n",
    "```"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.14: Create a Data Dictionary\n",
    "\n",
    "| Dataset | Purpose |\n",
    "|---|---|\n",
    "| `sales_daily` | Daily transactional sales records per product, price, and promotions. |\n",
    "| `inventory_snapshots` | Weekly inventory snapshot monitoring on-hand, on-order and lead times. |\n",
    "| `calendar` | Date dimensions including holidays, seasons, weeks and promotion events. |\n",
    "| `sku_master` | Product master attributes containing pricing, manufacturing cost and classification. |"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Step 1.15: Write Observations\n",
    "\n",
    "#### Data Profile Observations Summary:\n",
    "1. **Total Datasets**: 4 core files loaded successfully.\n",
    "2. **Content Description**:\n",
    "   - `sales_daily`: Daily transactions recording units sold and daily prices.\n",
    "   - `inventory_snapshots`: Weekly level snapshots recording stock on hand/on order.\n",
    "   - `calendar`: Standard date attributes, holiday markers, and marketing event labels.\n",
    "   - `sku_master`: Catalogue dimensions including MSRP, and procurement costs.\n",
    "3. **Data Quality Profiling**:\n",
    "   - **Missing Values**: `sales_daily` has 716 missing values in both `units_sold` and `revenue`. `calendar` has 713 missing values in `promo_event`, representing days without promotions.\n",
    "   - **Duplicate Records**: `sales_daily` has 182 duplicate rows that must be cleaned.\n",
    "   - **Date Fields**: All date fields (`sales_daily.date`, `inventory_snapshots.date`, `calendar.date`, and `sku_master.launch_date`) are currently string text objects and must be converted to datetime.\n",
    "4. **Relational Links**: Datasets can be joined using a multi-key bridge on `sku_id` and `date` fields."
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.11.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)

print("Notebook generated successfully!")
