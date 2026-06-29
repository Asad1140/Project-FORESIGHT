# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Ingestion and Forecasting Data Service
---------------------------------------------------------
Handles loading, caching, and validating core data frames and model forecast results.
Raises explicit exceptions when files are missing to avoid fake/fallback values.
"""

import os
import json
import logging
from typing import Tuple, Dict, Any, Optional
import pandas as pd
from data_prep import clean_and_validate_data
from config import (
    DATA_DIR,
    CLEAN_SALES_CSV,
    CLEAN_CALENDAR_CSV,
    CLEAN_SKU_MASTER_CSV,
    CLEAN_INVENTORY_CSV,
    FORECAST_RESULTS_CSV,
    FORECAST_METRICS_JSON,
    PIPELINE_RUN_LOG_JSON
)

logger = logging.getLogger(__name__)


class ForecastDataMissingError(FileNotFoundError):
    """Exception raised when required forecasting result files are missing."""
    pass


def load_base_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads pre-cleaned CSV data files if they exist to optimize performance.
    If any clean file is missing, it runs the data prep pipeline to generate them.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            SKU, Sales, Calendar, and Inventory dataframes.
    """
    logger.info("Service: loading base datasets...")
    clean_files = [CLEAN_SKU_MASTER_CSV, CLEAN_SALES_CSV, CLEAN_CALENDAR_CSV, CLEAN_INVENTORY_CSV]
    
    if all(os.path.exists(f) for f in clean_files):
        logger.info("Loading pre-cleaned base datasets from disk...")
        sku = pd.read_csv(CLEAN_SKU_MASTER_CSV)
        sales = pd.read_csv(CLEAN_SALES_CSV)
        calendar = pd.read_csv(CLEAN_CALENDAR_CSV)
        inventory = pd.read_csv(CLEAN_INVENTORY_CSV)
        
        # Convert date columns to datetime
        sales["date"] = pd.to_datetime(sales["date"])
        calendar["date"] = pd.to_datetime(calendar["date"])
        inventory["date"] = pd.to_datetime(inventory["date"])
        sku["launch_date"] = pd.to_datetime(sku["launch_date"])
        
        return sku, sales, calendar, inventory
        
    logger.warning("Cleaned base datasets not found. Running preparation pipeline...")
    sku, sales, calendar, inventory = clean_and_validate_data(DATA_DIR)
    return sku, sales, calendar, inventory


def load_forecast_data() -> Tuple[pd.DataFrame, Dict[str, float], Dict[str, Any]]:
    """
    Loads forecasting results and pipeline metrics from CSV and JSON files.
    Raises ForecastDataMissingError if any crucial files are missing.

    Returns:
        Tuple[pd.DataFrame, Dict[str, float], Dict[str, Any]]:
            Forecast Results DataFrame, WAPE Metrics dictionary, and Pipeline Log dictionary.

    Raises:
        ForecastDataMissingError: If forecast CSV, metrics JSON, or pipeline log JSON is missing.
    """
    logger.info("Service: loading forecast datasets and logs...")

    # Validate file existences
    missing_files = []
    if not os.path.exists(FORECAST_RESULTS_CSV):
        missing_files.append(FORECAST_RESULTS_CSV)
    if not os.path.exists(FORECAST_METRICS_JSON):
        missing_files.append(FORECAST_METRICS_JSON)
    if not os.path.exists(PIPELINE_RUN_LOG_JSON):
        missing_files.append(PIPELINE_RUN_LOG_JSON)

    if missing_files:
        error_msg = f"Missing required forecast files: {', '.join(missing_files)}"
        logger.error(error_msg)
        raise ForecastDataMissingError(error_msg)

    try:
        # Load Forecast Results
        fc_results = pd.read_csv(FORECAST_RESULTS_CSV)
        fc_results["date"] = pd.to_datetime(fc_results["date"])
        
        # Load Forecast Metrics
        with open(FORECAST_METRICS_JSON, "r", encoding="utf-8") as f:
            metrics = json.load(f)
            
        # Load Pipeline Audit Log
        with open(PIPELINE_RUN_LOG_JSON, "r", encoding="utf-8") as f:
            pipeline_log = json.load(f)
            
        logger.info("Forecast data and logs loaded successfully.")
        return fc_results, metrics, pipeline_log

    except Exception as e:
        logger.error(f"Error loading forecasting data files: {str(e)}")
        raise ForecastDataMissingError(f"Corrupted or invalid forecast files: {str(e)}")
