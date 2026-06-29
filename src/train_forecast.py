# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Model Training & Forecasting Pipeline
---------------------------------------------------------
Trains a Random Forest forecasting model on weekly aggregated sales,
evaluates WAPE against a seasonal-naive baseline on a backtest period,
and projects future demand with confidence intervals.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder
import joblib

# Import custom feature engineering module
from feature_engineering import engineer_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def calculate_metrics(actual: np.ndarray, forecast: np.ndarray) -> Dict[str, float]:
    """
    Calculates regression evaluation metrics (WAPE, MAE, RMSE, Bias).

    Args:
        actual (np.ndarray): True values.
        forecast (np.ndarray): Predicted values.

    Returns:
        Dict[str, float]: Computed metrics.
    """
    abs_errors = np.abs(actual - forecast)
    sum_actuals = np.sum(actual)
    
    wape = float(np.sum(abs_errors) / sum_actuals) if sum_actuals > 0 else 0.0
    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean((actual - forecast) ** 2)))
    # Signed Bias as percentage of total actuals
    bias = float(np.sum(forecast - actual) / sum_actuals) if sum_actuals > 0 else 0.0
    
    return {
        "wape": wape,
        "mae": mae,
        "rmse": rmse,
        "bias": bias
    }


def compute_recursive_features(
    sku_id: str,
    date: pd.Timestamp,
    sales_lookup: Dict[Tuple[str, pd.Timestamp], float],
    calendar_df: pd.DataFrame,
    sku_row: pd.Series
) -> Dict[str, Any]:
    """
    Computes all 19 features recursively for a given SKU and future date.

    Args:
        sku_id (str): Unique SKU identifier.
        date (pd.Timestamp): Target forecast date.
        sales_lookup (Dict[Tuple[str, pd.Timestamp], float]): Lookup map of sales.
        calendar_df (pd.DataFrame): Cleaned calendar DataFrame.
        sku_row (pd.Series): Row containing SKU master attributes.

    Returns:
        Dict[str, Any]: Feature dictionary.
    """
    # 1. Lags
    lag_1 = sales_lookup.get((sku_id, date - pd.to_timedelta(7, unit='D')), 0.0)
    lag_7 = sales_lookup.get((sku_id, date - pd.to_timedelta(49, unit='D')), 0.0)
    lag_14 = sales_lookup.get((sku_id, date - pd.to_timedelta(98, unit='D')), 0.0)
    lag_28 = sales_lookup.get((sku_id, date - pd.to_timedelta(196, unit='D')), 0.0)

    # 2. Rolling stats (based on past 7 weeks)
    past_7_weeks = [
        sales_lookup.get((sku_id, date - pd.to_timedelta(7 * i, unit='D')), 0.0)
        for i in range(1, 8)
    ]
    rolling_mean = float(np.mean(past_7_weeks))
    rolling_std = float(np.std(past_7_weeks)) if len(past_7_weeks) > 1 else 0.0
    rolling_max = float(np.max(past_7_weeks))
    rolling_min = float(np.min(past_7_weeks))

    # 3. Calendar features
    day_of_week = 6  # Always Sunday for weekly demand ending on Sunday
    week_number = int(date.isocalendar().week)
    month = int(date.month)
    quarter = int(date.quarter)
    weekend_flag = 1  # Weekly demand always includes weekends

    # 4. Holiday & Promotion flags
    # Get all days in the week ending on 'date'
    week_days = pd.date_range(end=date, periods=7, freq='D')
    week_calendar = calendar_df[calendar_df["date"].isin(week_days)]
    
    holiday_flag = int(week_calendar["is_holiday"].max() > 0) if not week_calendar.empty else 0
    # Promotions: check if there's any promotion event or flag
    promo_flag = 0
    if not week_calendar.empty and "promo_event" in week_calendar.columns:
        promo_flag = int(week_calendar["promo_event"].notnull().any())

    return {
        "unit_cost": float(sku_row["unit_cost"]),
        "list_price": float(sku_row["list_price"]),
        "category_encoded": int(sku_row["category_encoded"]),
        "subcategory_encoded": int(sku_row["subcategory_encoded"]),
        "lag_1": lag_1,
        "lag_7": lag_7,
        "lag_14": lag_14,
        "lag_28": lag_28,
        "rolling_mean": rolling_mean,
        "rolling_std": rolling_std,
        "rolling_max": rolling_max,
        "rolling_min": rolling_min,
        "rolling_mean_7": rolling_mean,
        "rolling_std_7": rolling_std,
        "rolling_max_7": rolling_max,
        "rolling_min_7": rolling_min,
        "day_of_week": day_of_week,
        "week_number": week_number,
        "month": month,
        "quarter": quarter,
        "holiday_flag": holiday_flag,
        "promo_flag": promo_flag,
        "promotion_flag": promo_flag,
        "weekend_flag": weekend_flag
    }


def train_and_evaluate(data_dir: str = "data") -> None:
    """
    Executes the training pipeline: loads data, engineers features, performs
    cross-validation, trains a Random Forest forecast, compares against baseline,
    and saves the models, results, and metrics.

    Args:
        data_dir (str): Directory containing cleaned files.
    """
    logger.info("Initializing Model Training & Forecasting Pipeline...")
    
    # 1. Load cleaned datasets
    sales_path = os.path.join(data_dir, "clean_sales.csv")
    calendar_path = os.path.join(data_dir, "clean_calendar.csv")
    sku_path = os.path.join(data_dir, "clean_sku_master.csv")
    
    if not all(os.path.exists(p) for p in [sales_path, calendar_path, sku_path]):
        raise FileNotFoundError("Cleaned sales, calendar, or SKU master datasets are missing. Run data prep first.")
        
    sales = pd.read_csv(sales_path)
    calendar = pd.read_csv(calendar_path)
    sku = pd.read_csv(sku_path)
    
    # Convert date columns
    sales["date"] = pd.to_datetime(sales["date"])
    calendar["date"] = pd.to_datetime(calendar["date"])
    sku["launch_date"] = pd.to_datetime(sku["launch_date"])

    # Reconstruct a complete daily grid of all SKUs and dates to avoid gaps
    logger.info("Reconstructing complete daily grid of all SKUs and dates...")
    all_skus = sku["sku_id"].unique()
    min_date = sales["date"].min()
    max_date = sales["date"].max()
    all_dates = pd.date_range(start=min_date, end=max_date, freq="D")
    
    grid = pd.MultiIndex.from_product([all_skus, all_dates], names=["sku_id", "date"]).to_frame().reset_index(drop=True)
    
    # Merge sales data
    daily_df = pd.merge(grid, sales, on=["sku_id", "date"], how="left")
    daily_df["units_sold"] = daily_df["units_sold"].fillna(0.0)
    daily_df["revenue"] = daily_df["revenue"].fillna(0.0)
    daily_df["unit_price"] = daily_df["unit_price"].fillna(0.0)
    daily_df["promo_flag"] = daily_df["promo_flag"].fillna(0.0).astype(int)
    
    # Merge calendar data
    daily_df = pd.merge(daily_df, calendar[["date", "is_holiday"]], on="date", how="left")
    daily_df["is_holiday"] = daily_df["is_holiday"].fillna(0.0).astype(int)

    # 2. Call feature_engineering.py
    logger.info("Calling feature engineering module on daily data...")
    daily_df = engineer_features(daily_df, target_col="units_sold", date_col="date")

    # 3. Aggregate daily sales into weekly demand
    logger.info("Aggregating daily sales to weekly demand...")
    daily_df["week_end"] = daily_df["date"] - pd.to_timedelta(daily_df["date"].dt.weekday, unit='D') + pd.to_timedelta(6, unit='D')
    
    weekly_data = daily_df.groupby(["sku_id", "week_end"]).agg({
        "units_sold": "sum",
        "lag_1": "sum",
        "lag_7": "sum",
        "lag_14": "sum",
        "lag_28": "sum",
        "rolling_mean_7": "mean",
        "rolling_std_7": "mean",
        "rolling_max_7": "mean",
        "rolling_min_7": "mean",
        "rolling_mean": "mean",
        "rolling_std": "mean",
        "rolling_max": "mean",
        "rolling_min": "mean",
        "day_of_week": "mean",
        "week_number": "first",
        "month": "first",
        "quarter": "first",
        "holiday_flag": "max",
        "promo_flag": "max",
        "promotion_flag": "max",
        "weekend_flag": "max"
    }).reset_index().rename(columns={"week_end": "date", "units_sold": "actual_sales"})

    # Merge SKU dimensions
    weekly_data = pd.merge(weekly_data, sku, on="sku_id", how="left")
    
    # Label encode categorical columns
    encoders = {}
    for col in ["category", "subcategory"]:
        le = LabelEncoder()
        weekly_data[f"{col}_encoded"] = le.fit_transform(weekly_data[col].astype(str))
        encoders[col] = le

    # 4. Sort chronologically
    weekly_data = weekly_data.sort_values(by=["sku_id", "date"]).reset_index(drop=True)

    # 5. Create a Seasonal Naive baseline
    logger.info("Creating Seasonal Naive baseline...")
    sales_lookup = weekly_data.set_index(["sku_id", "date"])["actual_sales"].to_dict()
    weekly_data["baseline_forecast"] = [
        sales_lookup.get((sku_id, d - pd.to_timedelta(364, unit='D')), 0.0)
        for sku_id, d in zip(weekly_data["sku_id"], weekly_data["date"])
    ]

    # Define feature columns
    feature_cols = [
        "unit_cost", "list_price", "category_encoded", "subcategory_encoded",
        "lag_1", "lag_7", "lag_14", "lag_28",
        "rolling_mean", "rolling_std", "rolling_max", "rolling_min",
        "day_of_week", "week_number", "month", "quarter",
        "holiday_flag", "promo_flag", "weekend_flag"
    ]

    # Split Train / Backtest / Future
    backtest_start_date = pd.to_datetime("2025-11-20")
    backtest_end_date = pd.to_datetime("2025-12-31")
    
    train_mask = weekly_data["date"] < backtest_start_date
    train_df = weekly_data[train_mask].copy()

    # 7. TimeSeriesSplit Cross Validation on Train Set
    logger.info("Performing TimeSeriesSplit Cross-Validation...")
    unique_train_weeks = sorted(train_df["date"].unique())
    tscv = TimeSeriesSplit(n_splits=5)
    
    cv_ml_preds = []
    cv_base_preds = []
    cv_actuals = []
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(unique_train_weeks)):
        fold_train_weeks = [unique_train_weeks[i] for i in train_idx]
        fold_val_weeks = [unique_train_weeks[i] for i in val_idx]
        
        fold_train = train_df[train_df["date"].isin(fold_train_weeks)]
        fold_val = train_df[train_df["date"].isin(fold_val_weeks)]
        
        if fold_train.empty or fold_val.empty:
            continue
            
        fold_model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        fold_model.fit(fold_train[feature_cols], fold_train["actual_sales"])
        
        preds = fold_model.predict(fold_val[feature_cols])
        
        cv_ml_preds.extend(preds)
        cv_base_preds.extend(fold_val["baseline_forecast"].values)
        cv_actuals.extend(fold_val["actual_sales"].values)
        
    cv_actuals_arr = np.array(cv_actuals)
    cv_ml_preds_arr = np.array(cv_ml_preds)
    cv_base_preds_arr = np.array(cv_base_preds)
    
    cv_ml_metrics = calculate_metrics(cv_actuals_arr, cv_ml_preds_arr)
    cv_base_metrics = calculate_metrics(cv_actuals_arr, cv_base_preds_arr)
    
    logger.info("Cross-Validation Results (averaged over folds):")
    logger.info(f"ML WAPE: {cv_ml_metrics['wape']:.2%} | Baseline WAPE: {cv_base_metrics['wape']:.2%}")

    # 6. Train RandomForestRegressor on all training data
    logger.info("Training final RandomForestRegressor model...")
    final_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    final_model.fit(train_df[feature_cols], train_df["actual_sales"])

    # Calculate standard deviation of residuals on the training set
    train_preds = final_model.predict(train_df[feature_cols])
    residuals = train_df["actual_sales"] - train_preds
    std_error = float(np.std(residuals))

    # Predict on the Backtest Period
    backtest_mask = (weekly_data["date"] >= backtest_start_date) & (weekly_data["date"] <= backtest_end_date)
    backtest_df = weekly_data[backtest_mask].copy()
    
    if not backtest_df.empty:
        backtest_df["ml_forecast"] = final_model.predict(backtest_df[feature_cols])
        backtest_df["lower_bound"] = np.maximum(0.0, backtest_df["ml_forecast"] - 1.28 * std_error)
        backtest_df["upper_bound"] = backtest_df["ml_forecast"] + 1.28 * std_error
    else:
        logger.warning("No backtest data found in the specified dates.")

    # 8. Evaluate on backtest period
    actual_bt = backtest_df["actual_sales"].values
    ml_bt = backtest_df["ml_forecast"].values
    base_bt = backtest_df["baseline_forecast"].values
    
    ml_metrics = calculate_metrics(actual_bt, ml_bt)
    base_metrics = calculate_metrics(actual_bt, base_bt)
    improvement = base_metrics["wape"] - ml_metrics["wape"]

    logger.info(f"--- Backtest Evaluation (Nov 20, 2025 - Dec 31, 2025) ---")
    logger.info(f"Baseline (Seasonal-Naive) WAPE : {base_metrics['wape']:.2%}")
    logger.info(f"ML (Random Forest) WAPE        : {ml_metrics['wape']:.2%}")
    logger.info(f"WAPE Improvement               : {improvement:.2%}")

    # Generate 6-Week Future Projections (Jan 1, 2026 to Feb 15, 2026)
    # The max date in the dataset is the start point for recursive forecasting
    max_weekly_date = weekly_data["date"].max()
    future_dates = pd.date_range(start=max_weekly_date + pd.to_timedelta(7, unit='D'), periods=6, freq="W")
    
    logger.info(f"Generating 6-week future projections starting from {future_dates[0]}...")
    
    # We will compute recursive forecasting week-by-week
    future_rows = []
    
    # Store temporary copy of sales lookup to update with future predictions
    future_sales_lookup = sales_lookup.copy()
    
    # Extract SKU master details as map
    sku_map = sku.set_index("sku_id")
    # Pre-map SKU encoded IDs
    sku_encoded_df = weekly_data[["sku_id", "category_encoded", "subcategory_encoded"]].drop_duplicates().set_index("sku_id")
    
    for step, future_date in enumerate(future_dates, start=1):
        step_rows = []
        for sku_id in all_skus:
            sku_master_row = sku_map.loc[sku_id]
            sku_enc_row = sku_encoded_df.loc[sku_id]
            sku_row = pd.concat([sku_master_row, sku_enc_row])
            
            # Compute features recursively
            feats = compute_recursive_features(
                sku_id=sku_id,
                date=future_date,
                sales_lookup=future_sales_lookup,
                calendar_df=calendar,
                sku_row=sku_row
            )
            feats["sku_id"] = sku_id
            feats["date"] = future_date
            step_rows.append(feats)
            
        step_df = pd.DataFrame(step_rows)
        # Predict sales for this step
        preds = final_model.predict(step_df[feature_cols])
        step_df["ml_forecast"] = preds
        
        # Calculate baseline forecast for future
        step_df["baseline_forecast"] = [
            sales_lookup.get((sku_id, future_date - pd.to_timedelta(364, unit='D')), 0.0)
            for sku_id in step_df["sku_id"]
        ]
        
        # Uncertainty propagates with horizon step
        step_std = std_error * np.sqrt(step)
        step_df["lower_bound"] = np.maximum(0.0, preds - 1.28 * step_std)
        step_df["upper_bound"] = preds + 1.28 * step_std
        step_df["actual_sales"] = np.nan
        
        # Add predictions to future lookup
        for sku_id, pred in zip(step_df["sku_id"], preds):
            future_sales_lookup[(sku_id, future_date)] = float(pred)
            
        future_rows.append(step_df)
        
    future_df = pd.concat(future_rows, ignore_index=True)

    # 10. Compile and Save forecast_results.csv
    logger.info("Compiling final forecast results...")
    
    # Historical data (excluding backtest and future)
    hist_mask = weekly_data["date"] < backtest_start_date
    hist_df = weekly_data[hist_mask].copy()
    hist_df["ml_forecast"] = np.nan
    hist_df["lower_bound"] = np.nan
    hist_df["upper_bound"] = np.nan
    
    # Combine hist, backtest, and future ensuring no duplication
    # Backtest and future have predictions, historical has actual sales only.
    result_df = pd.concat([
        hist_df[["date", "sku_id", "actual_sales", "baseline_forecast", "ml_forecast", "lower_bound", "upper_bound"]],
        backtest_df[["date", "sku_id", "actual_sales", "baseline_forecast", "ml_forecast", "lower_bound", "upper_bound"]],
        future_df[["date", "sku_id", "actual_sales", "baseline_forecast", "ml_forecast", "lower_bound", "upper_bound"]]
    ], ignore_index=True)
    
    # Add UI required columns to avoid dashboard crash
    result_df["ml_lower_bound"] = result_df["lower_bound"]
    result_df["ml_upper_bound"] = result_df["upper_bound"]
    result_df["std_error"] = (result_df["upper_bound"] - result_df["ml_forecast"]) / 1.28
    result_df["std_error"] = result_df["std_error"].fillna(0.0)
    
    result_df = result_df.sort_values(by=["sku_id", "date"]).reset_index(drop=True)
    
    # Save forecast results to data/forecast_results.csv
    os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)
    results_path = os.path.join(data_dir, "forecast_results.csv")
    result_df.to_csv(results_path, index=False)
    logger.info(f"Forecast results saved to {results_path}")
    
    # Save directly to project root for deliverables checklist
    root_results_path = os.path.join(PROJECT_ROOT, "forecast_results.csv")
    result_df.to_csv(root_results_path, index=False)

    # Save metrics JSON
    metrics_payload = {
        "model": "RandomForestRegressor",
        "baseline_wape": float(base_metrics["wape"]),
        "ml_wape": float(ml_metrics["wape"]),
        "mae": float(ml_metrics["mae"]),
        "rmse": float(ml_metrics["rmse"]),
        "bias": float(ml_metrics["bias"]),
        "improvement": float(improvement),
        "training_date": pd.Timestamp.now().strftime("%Y-%m-%d")
    }
    
    # Save to data/logs/forecast_metrics.json (expected by UI)
    ui_metrics_path = os.path.join(data_dir, "logs", "forecast_metrics.json")
    os.makedirs(os.path.dirname(ui_metrics_path), exist_ok=True)
    with open(ui_metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=4)
    logger.info(f"Evaluation metrics saved to {ui_metrics_path}")
    
    # Save to logs/forecast_metrics.json (requested by user)
    logs_metrics_path = os.path.join(PROJECT_ROOT, "logs", "forecast_metrics.json")
    os.makedirs(os.path.dirname(logs_metrics_path), exist_ok=True)
    with open(logs_metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=4)
    logger.info(f"Evaluation metrics saved to {logs_metrics_path}")

    # Save directly to project root for deliverables checklist
    root_metrics_path = os.path.join(PROJECT_ROOT, "forecast_metrics.json")
    with open(root_metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=4)

    # Serialize model assets
    model_assets = {
        "model": final_model,
        "std_error": std_error,
        "feature_cols": feature_cols,
        "encoders": encoders
    }
    
    # Save model to models/forecast_model.pkl
    root_model_dir = os.path.join(PROJECT_ROOT, "models")
    os.makedirs(root_model_dir, exist_ok=True)
    logs_model_path = os.path.join(root_model_dir, "forecast_model.pkl")
    joblib.dump(model_assets, logs_model_path)
    logger.info(f"Model serialized and saved to {logs_model_path}")
    
    # Save directly to project root for deliverables checklist
    root_model_path = os.path.join(PROJECT_ROOT, "forecast_model.pkl")
    joblib.dump(model_assets, root_model_path)

    # Also save to data/models/forecast_model.pkl (expected by UI / config)
    ui_model_path = os.path.join(data_dir, "models", "forecast_model.pkl")
    os.makedirs(os.path.dirname(ui_model_path), exist_ok=True)
    joblib.dump(model_assets, ui_model_path)
    
    # Backup directly under data/forecast_model.pkl just in case
    data_model_path = os.path.join(data_dir, "forecast_model.pkl")
    joblib.dump(model_assets, data_model_path)


if __name__ == "__main__":
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_data_dir = os.path.join(PROJECT_ROOT, "data")
    if not os.path.exists(target_data_dir):
        target_data_dir = "data"
    train_and_evaluate(target_data_dir)
