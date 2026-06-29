# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Centralized Configuration File
------------------------------------------------
Defines file paths, log locations, styling details, and key project directories.
"""

import os

# Project root directory detection
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Centralized Directory Structure
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
MODEL_DIR = os.path.join(DATA_DIR, "models")
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports")

# Ensure critical directories exist
for folder in [DATA_DIR, LOG_DIR, MODEL_DIR, REPORT_DIR]:
    os.makedirs(folder, exist_ok=True)

# Raw Data Path Definitions
SALES_DAILY_CSV = os.path.join(DATA_DIR, "sales_daily.csv")
CALENDAR_CSV = os.path.join(DATA_DIR, "calendar.csv")
SKU_MASTER_CSV = os.path.join(DATA_DIR, "sku_master.csv")
INVENTORY_SNAPSHOTS_CSV = os.path.join(DATA_DIR, "inventory_snapshots.csv")

# Clean Data Path Definitions
CLEAN_SALES_CSV = os.path.join(DATA_DIR, "clean_sales.csv")
CLEAN_CALENDAR_CSV = os.path.join(DATA_DIR, "clean_calendar.csv")
CLEAN_SKU_MASTER_CSV = os.path.join(DATA_DIR, "clean_sku_master.csv")
CLEAN_INVENTORY_CSV = os.path.join(DATA_DIR, "clean_inventory.csv")

# Outputs and Logs
FORECAST_RESULTS_CSV = os.path.join(DATA_DIR, "forecast_results.csv")
FORECAST_METRICS_JSON = os.path.join(DATA_DIR, "logs", "forecast_metrics.json")
PIPELINE_RUN_LOG_JSON = os.path.join(DATA_DIR, "logs", "pipeline_run_log.json")
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Streamlit Premium Styling CSS & Color Config
COLOR_MAP = {
    "REORDER NOW": "#ef4444",
    "MARKDOWN / CLEAR": "#a855f7",
    "WATCH / VOLATILE": "#f59e0b",
    "HEALTHY": "#10b981"
}

# Gauge Threshold color configurations
GAUGE_STEPS = [
    {"range": [0, 1.0], "color": "rgba(239, 68, 68, 0.15)"},
    {"range": [1.0, 1.5], "color": "rgba(16, 185, 129, 0.15)"}
]
