# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Automated QA & Pipeline Unit Tests
------------------------------------------------------
Verifies feature engineering, risk scoring, data ingestion, and pipeline health.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np

# Add src/ folder to sys.path to resolve module imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from feature_engineering import engineer_features
from risk_engine import calculate_risk_scoring
from forecast_service import load_base_data, load_forecast_data


class TestPipeline(unittest.TestCase):
    """Unit test suite for validating pipeline functions and preventing regressions."""

    def setUp(self) -> None:
        """Sets up mock daily sales and inventory datasets for validation tests."""
        # Create a mock daily sales dataframe for a single SKU
        dates = pd.date_range(start="2025-01-01", periods=40, freq="D")
        self.mock_daily_sales = pd.DataFrame({
            "date": dates,
            "sku_id": ["SKU_TEST"] * 40,
            "units_sold": [float(i % 10) for i in range(40)],
            "revenue": [float(i % 10 * 100) for i in range(40)],
            "unit_price": [100.0] * 40,
            "promo_flag": [i % 5 == 0 for i in range(40)],
            "is_holiday": [i % 15 == 0 for i in range(40)]
        })

        # Create a mock inventory dataframe
        self.mock_inventory = pd.DataFrame({
            "date": [pd.Timestamp("2025-02-09")],
            "sku_id": ["SKU_TEST"],
            "on_hand_units": [20.0],
            "on_order_units": [10.0],
            "lead_time_days": [14],
            "reorder_point": [15]
        })

        # Create a mock SKU master dataframe
        self.mock_sku = pd.DataFrame({
            "sku_id": ["SKU_TEST"],
            "category": ["Kitchenware"],
            "subcategory": ["Cookware"],
            "unit_cost": [50.0],
            "list_price": [100.0],
            "launch_date": [pd.Timestamp("2024-01-01")]
        })

    def test_feature_engineering_output(self) -> None:
        """Verifies that feature engineering runs and generates all 15 required features."""
        df_feat = engineer_features(self.mock_daily_sales.copy(), target_col="units_sold", date_col="date")
        
        # Required features list
        required_cols = [
            "lag_1", "lag_7", "lag_14", "lag_28",
            "rolling_mean_7", "rolling_std_7", "rolling_max_7", "rolling_min_7",
            "rolling_mean", "rolling_std", "rolling_max", "rolling_min",
            "day_of_week", "week_number", "month", "quarter",
            "holiday_flag", "promo_flag", "weekend_flag"
        ]
        
        for col in required_cols:
            self.assertIn(col, df_feat.columns, f"Required feature '{col}' is missing from output columns.")

        # Validate weekend flag is 1 for Saturday/Sunday
        saturday_idx = df_feat[df_feat["day_of_week"] == 5].index
        sunday_idx = df_feat[df_feat["day_of_week"] == 6].index
        
        self.assertTrue((df_feat.loc[saturday_idx, "weekend_flag"] == 1).all())
        self.assertTrue((df_feat.loc[sunday_idx, "weekend_flag"] == 1).all())

        # Validate weekday has weekend flag 0
        monday_idx = df_feat[df_feat["day_of_week"] == 0].index
        self.assertTrue((df_feat.loc[monday_idx, "weekend_flag"] == 0).all())

    def test_risk_scoring_zero_sales(self) -> None:
        """Verifies that risk calculations do not crash or produce division-by-zero on low/zero sales."""
        # Create zero sales scenario
        zero_sales = self.mock_daily_sales.copy()
        zero_sales["units_sold"] = 0.0
        
        risk_df = calculate_risk_scoring(
            latest_inventory=self.mock_inventory,
            sku_df=self.mock_sku,
            sales_df=zero_sales,
            safety_stock_weeks=1.5,
            lt_override=False
        )
        
        # Verify no NaN or Inf values in core risk scores
        self.assertFalse(np.isinf(risk_df["overstock_risk"]).any(), "Overstock risk contains infinite values.")
        self.assertFalse(np.isnan(risk_df["overstock_risk"]).any(), "Overstock risk contains NaN values.")
        self.assertFalse(np.isinf(risk_df["stockout_risk"]).any(), "Stockout risk contains infinite values.")
        self.assertFalse(np.isnan(risk_df["stockout_risk"]).any(), "Stockout risk contains NaN values.")


if __name__ == "__main__":
    unittest.main()
