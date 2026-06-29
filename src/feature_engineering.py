# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Feature Engineering Module
---------------------------------------------
Generates lag, rolling window, calendar, and categorical features
for the demand forecasting machine learning model.
"""

import logging
from typing import List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)


def add_lag_features(df: pd.DataFrame, target_col: str, lags: List[int]) -> pd.DataFrame:
    """
    Creates lag features for the specified target column grouped by SKU.

    Args:
        df (pd.DataFrame): Input DataFrame (must contain 'sku_id' and date_col).
        target_col (str): The column to lag.
        lags (List[int]): List of lag steps to apply.

    Returns:
        pd.DataFrame: DataFrame with new lag features.
    """
    for lag in lags:
        col_name = f"lag_{lag}"
        df[col_name] = df.groupby("sku_id")[target_col].shift(lag).fillna(0.0)
    return df


def add_rolling_features(df: pd.DataFrame, target_col: str, window: int = 7) -> pd.DataFrame:
    """
    Creates rolling window statistics (Mean, Std, Max, Min) on lagged target
    to prevent data leakage.

    Args:
        df (pd.DataFrame): Input DataFrame.
        target_col (str): The target column (e.g. 'units_sold') to calculate rolling metrics on.
        window (int): Window size (in days/weeks) for the rolling calculation.

    Returns:
        pd.DataFrame: DataFrame with new rolling features.
    """
    # Shift target by 1 first to prevent leakage
    shifted = df.groupby("sku_id")[target_col].shift(1)

    df[f"rolling_mean_{window}"] = (
        shifted.groupby(df["sku_id"])
        .transform(lambda x: x.rolling(window, min_periods=1).mean())
        .fillna(0.0)
    )
    df[f"rolling_std_{window}"] = (
        shifted.groupby(df["sku_id"])
        .transform(lambda x: x.rolling(window, min_periods=1).std())
        .fillna(0.0)
    )
    df[f"rolling_max_{window}"] = (
        shifted.groupby(df["sku_id"])
        .transform(lambda x: x.rolling(window, min_periods=1).max())
        .fillna(0.0)
    )
    df[f"rolling_min_{window}"] = (
        shifted.groupby(df["sku_id"])
        .transform(lambda x: x.rolling(window, min_periods=1).min())
        .fillna(0.0)
    )

    # Aliases without window size suffix for flexibility
    df["rolling_mean"] = df[f"rolling_mean_{window}"]
    df["rolling_std"] = df[f"rolling_std_{window}"]
    df["rolling_max"] = df[f"rolling_max_{window}"]
    df["rolling_min"] = df[f"rolling_min_{window}"]

    return df


def add_calendar_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Extracts time-based features from a date column.

    Args:
        df (pd.DataFrame): Input DataFrame.
        date_col (str): Name of the date column.

    Returns:
        pd.DataFrame: DataFrame with temporal columns.
    """
    dates = pd.to_datetime(df[date_col])
    df["day_of_week"] = dates.dt.dayofweek
    df["week_number"] = dates.dt.isocalendar().week.astype(int)
    df["month"] = dates.dt.month
    df["quarter"] = dates.dt.quarter
    df["weekend_flag"] = dates.dt.dayofweek.isin([5, 6]).astype(int)
    return df


def add_categorical_encodings(
    df: pd.DataFrame, categorical_cols: List[str]
) -> Tuple[pd.DataFrame, dict]:
    """
    Applies Label Encoding to categorical features.

    Args:
        df (pd.DataFrame): Input DataFrame.
        categorical_cols (List[str]): Columns to encode.

    Returns:
        Tuple[pd.DataFrame, dict]: Encoded DataFrame and a dictionary of fitted LabelEncoders.
    """
    encoders = {}
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            # Handle NaN values by converting to string first
            df[f"{col}_encoded"] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
            logger.info(f"Encoded column: {col} -> {col}_encoded")
    return df, encoders


def engineer_features(df: pd.DataFrame, target_col: str = "units_sold", date_col: str = "date") -> pd.DataFrame:
    """
    Applies the full feature engineering pipeline: lags, rolling stats, calendar features,
    holiday/promo flags, and weekend flags.

    Args:
        df (pd.DataFrame): Input dataframe.
        target_col (str): Target column for lags and rolling window features.
        date_col (str): Date-like index column (usually 'date').

    Returns:
        pd.DataFrame: Feature-engineered DataFrame.
    """
    logger.info("Starting Feature Engineering Pipeline...")
    
    # Sort to ensure calculations along time series are correct
    df = df.sort_values(by=["sku_id", date_col]).reset_index(drop=True)
    
    # 1. Add Lags (1, 7, 14, 28)
    df = add_lag_features(df, target_col=target_col, lags=[1, 7, 14, 28])
    
    # 2. Add Rolling Features (Rolling window of 7)
    df = add_rolling_features(df, target_col=target_col, window=7)
    
    # 3. Add Temporal Features (day_of_week, week_number, month, quarter, weekend_flag)
    df = add_calendar_features(df, date_col=date_col)
    
    # 4. Add Holiday and Promotion flags
    if "is_holiday" in df.columns:
        df["holiday_flag"] = df["is_holiday"].astype(int)
    elif "holiday_flag" in df.columns:
        df["holiday_flag"] = df["holiday_flag"].astype(int)
    else:
        df["holiday_flag"] = 0
        
    if "promo_flag" in df.columns:
        df["promo_flag"] = df["promo_flag"].astype(int)
    elif "promotion_flag" in df.columns:
        df["promo_flag"] = df["promotion_flag"].astype(int)
    else:
        df["promo_flag"] = 0

    # Ensure promotion_flag is also present
    df["promotion_flag"] = df["promo_flag"]
    
    logger.info("Feature engineering complete.")
    return df
