# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Centralized Configuration File
------------------------------------------------
Defines file paths, log locations, styling details, and key project directories.
"""

from pathlib import Path

# Project root directory detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Centralized Directory Structure
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"
MODEL_DIR = PROJECT_ROOT / "models"
REPORT_DIR = PROJECT_ROOT / "reports"

# Ensure critical directories exist
for folder in [DATA_DIR, LOG_DIR, MODEL_DIR, REPORT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Raw Data Path Definitions
SALES_DAILY_CSV = DATA_DIR / "sales_daily.csv"
CALENDAR_CSV = DATA_DIR / "calendar.csv"
SKU_MASTER_CSV = DATA_DIR / "sku_master.csv"
INVENTORY_SNAPSHOTS_CSV = DATA_DIR / "inventory_snapshots.csv"

# Clean Data Path Definitions
CLEAN_SALES_CSV = DATA_DIR / "clean_sales.csv"
CLEAN_CALENDAR_CSV = DATA_DIR / "clean_calendar.csv"
CLEAN_SKU_MASTER_CSV = DATA_DIR / "clean_sku_master.csv"
CLEAN_INVENTORY_CSV = DATA_DIR / "clean_inventory.csv"

# Outputs and Logs
FORECAST_RESULTS_CSV = DATA_DIR / "forecast_results.csv"
FORECAST_METRICS_JSON = LOG_DIR / "forecast_metrics.json"
PIPELINE_RUN_LOG_JSON = LOG_DIR / "pipeline_run_log.json"
FORECAST_MODEL_PKL = MODEL_DIR / "forecast_model.pkl"
APP_LOG_FILE = LOG_DIR / "app.log"

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
