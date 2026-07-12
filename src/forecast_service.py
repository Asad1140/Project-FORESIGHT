# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Ingestion and Forecasting Data Service
---------------------------------------------------------
Handles loading, caching, and validating core data frames and model forecast results.
Raises explicit exceptions when files are missing to avoid fake/fallback values.
"""

from pathlib import Path
import json
import logging
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import joblib
from data_prep import clean_and_validate_data
from config import (
    DATA_DIR,
    CLEAN_SALES_CSV,
    CLEAN_CALENDAR_CSV,
    CLEAN_SKU_MASTER_CSV,
    CLEAN_INVENTORY_CSV,
    FORECAST_RESULTS_CSV,
    FORECAST_METRICS_JSON,
    PIPELINE_RUN_LOG_JSON,
    FORECAST_MODEL_PKL
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
    
    # Log absolute paths of all base files
    for f in clean_files:
        logger.info(f"Checking base file path: {Path(f).resolve()}")

    if all(Path(f).exists() for f in clean_files):
        logger.info("Loading pre-cleaned base datasets from disk...")
        sku = pd.read_csv(Path(CLEAN_SKU_MASTER_CSV))
        sales = pd.read_csv(Path(CLEAN_SALES_CSV))
        calendar = pd.read_csv(Path(CLEAN_CALENDAR_CSV))
        inventory = pd.read_csv(Path(CLEAN_INVENTORY_CSV))
        
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
    Loads forecasting results, model metrics, and pipeline logs.
    Performs detailed validation on existence, schema, and model serialization.

    Returns:
        Tuple[pd.DataFrame, Dict[str, float], Dict[str, Any]]:
            Forecast Results DataFrame, WAPE Metrics dictionary, and Pipeline Log dictionary.

    Raises:
        FileNotFoundError: If any required forecasting file or model is missing.
        ValueError: If files are corrupted, have missing columns/keys, or fail to load.
    """
    logger.info("Service: loading forecast datasets and logs...")

    # Log absolute paths of all loaded files
    logger.info(f"Loading:\n{Path(FORECAST_RESULTS_CSV).resolve()}")
    logger.info(f"Loading:\n{Path(FORECAST_METRICS_JSON).resolve()}")
    logger.info(f"Loading:\n{Path(PIPELINE_RUN_LOG_JSON).resolve()}")
    logger.info(f"Loading:\n{Path(FORECAST_MODEL_PKL).resolve()}")

    # Validate file existences using pathlib.Path
    missing_files = []
    for filepath, desc in [
        (FORECAST_RESULTS_CSV, "Forecast Results CSV"),
        (FORECAST_METRICS_JSON, "Forecast Metrics JSON"),
        (PIPELINE_RUN_LOG_JSON, "Pipeline Run Log JSON"),
        (FORECAST_MODEL_PKL, "Forecast Model PKL")
    ]:
        if not Path(filepath).exists():
            missing_files.append(f"{desc} (Searched: {Path(filepath).resolve()})")

    if missing_files:
        error_msg = f"Missing required forecast pipeline files: {', '.join(missing_files)}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # 1. Load and validate forecast_results.csv
    try:
        fc_results = pd.read_csv(Path(FORECAST_RESULTS_CSV))
    except Exception as e:
        logger.exception(f"Failed to parse forecast results CSV at {Path(FORECAST_RESULTS_CSV).resolve()}.")
        raise ValueError(f"CSVParserError: Failed to parse forecast_results.csv at {Path(FORECAST_RESULTS_CSV).resolve()}: {str(e)}") from e

    required_cols = ["date", "sku_id", "actual_sales", "baseline_forecast", "ml_forecast", "ml_upper_bound", "ml_lower_bound"]
    missing_cols = [col for col in required_cols if col not in fc_results.columns]
    if missing_cols:
        logger.error(f"Missing columns in forecast_results.csv: {missing_cols}")
        raise ValueError(f"MissingColumnsError: forecast_results.csv is missing required columns: {missing_cols}")

    try:
        fc_results["date"] = pd.to_datetime(fc_results["date"])
    except Exception as e:
        logger.exception("Failed to convert date column to datetime.")
        raise ValueError(f"TypeError: Invalid date values in forecast_results.csv: {str(e)}") from e

    # 2. Load and validate forecast_metrics.json
    try:
        with Path(FORECAST_METRICS_JSON).open("r", encoding="utf-8") as f:
            metrics = json.load(f)
    except json.JSONDecodeError as e:
        logger.exception(f"JSONDecodeError on forecast_metrics.json at {Path(FORECAST_METRICS_JSON).resolve()}")
        raise ValueError(f"JSONDecodeError: Failed to parse forecast_metrics.json at {Path(FORECAST_METRICS_JSON).resolve()}: {e.msg} (line {e.lineno}, col {e.colno})") from e
    except Exception as e:
        logger.exception(f"Unexpected error reading forecast_metrics.json at {Path(FORECAST_METRICS_JSON).resolve()}")
        raise ValueError(f"IOError: Failed to read forecast_metrics.json at {Path(FORECAST_METRICS_JSON).resolve()}: {str(e)}") from e

    required_keys = ["model", "baseline_wape", "ml_wape", "mae", "rmse", "bias", "improvement", "training_date"]
    missing_keys = [key for key in required_keys if key not in metrics]
    if missing_keys:
        logger.error(f"Missing expected keys in forecast_metrics.json: {missing_keys}")
        raise ValueError(f"KeyError: forecast_metrics.json is missing required keys: {missing_keys}")

    # 3. Load and validate pipeline_run_log.json
    try:
        with Path(PIPELINE_RUN_LOG_JSON).open("r", encoding="utf-8") as f:
            pipeline_log = json.load(f)
    except json.JSONDecodeError as e:
        logger.exception(f"JSONDecodeError on pipeline_run_log.json at {Path(PIPELINE_RUN_LOG_JSON).resolve()}")
        raise ValueError(f"JSONDecodeError: Failed to parse pipeline_run_log.json at {Path(PIPELINE_RUN_LOG_JSON).resolve()}: {e.msg} (line {e.lineno}, col {e.colno})") from e
    except Exception as e:
        logger.exception(f"Unexpected error reading pipeline_run_log.json at {Path(PIPELINE_RUN_LOG_JSON).resolve()}")
        raise ValueError(f"IOError: Failed to read pipeline_run_log.json at {Path(PIPELINE_RUN_LOG_JSON).resolve()}: {str(e)}") from e

    # 4. Load and validate forecast_model.pkl using joblib
    try:
        model_assets = joblib.load(Path(FORECAST_MODEL_PKL))
        if not isinstance(model_assets, dict) or "model" not in model_assets:
            raise ValueError("Deserialized model asset is not in the expected format (dict containing 'model' key).")
    except Exception as e:
        logger.exception(f"ModelLoadError on forecast_model.pkl at {Path(FORECAST_MODEL_PKL).resolve()}")
        raise ValueError(f"ModelLoadError: Failed to load forecast_model.pkl at {Path(FORECAST_MODEL_PKL).resolve()}: {str(e)}") from e

    logger.info("Forecast data, evaluation metrics, and model loaded and validated successfully.")
    return fc_results, metrics, pipeline_log
