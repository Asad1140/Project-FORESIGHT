# LINKEDIN ANNOUNCEMENT: PROJECT FORESIGHT
**Demand & Inventory Intelligence System for DTC Retail**

Below is a professional, engaging announcement drafted for LinkedIn to showcase the achievements and results of Project FORESIGHT.

---

### LinkedIn Post Draft

🚀 I’m excited to share my latest machine learning and decision-intelligence project: **Project FORESIGHT – Demand & Inventory Intelligence**!

DTC brands often struggle with inventory management, balancing the cost of stockouts on bestsellers against capital tied up in slow-moving overstock. Project FORESIGHT addresses this by replacing intuition-based planning with a reproducible, automated data and forecasting pipeline.

### 🛠️ Technical Highlights:
*   **Data Quality & Preprocessing**: Engineered an automated data cleaning and quality auditing pipeline (with IQR-based outlier capping and revenue validation) to clean 90,000+ daily sales records.
*   **Feature Engineering**: Generated 15 time-series features (including daily lags 1, 7, 14, 28, rolling window statistics, holiday indicators, and promotion flags).
*   **Forecasting Engine**: Trained a **Random Forest Regressor** in **Python** using chronological **TimeSeriesSplit** cross-validation to prevent temporal look-ahead leakage.
*   **Recursive Multi-Step Projections**: Implemented a recursive 6-week forecasting model with confidence bands to model uncertainty propagation.
*   **Interactive Streamlit Dashboard**: Integrated Plotly visualizations showing SKU risk matrix scatter plots, reorder priority tables, and inventory gauges.

### 📈 Results & Business Impact:
*   **WAPE Improvement**: Achieved a **9.86% WAPE** on the backtest period, outperforming the Seasonal-Naive baseline (WAPE of 23.46%) by **13.60%**.
*   **Optimized Replenishment**: Automates SKU classification into decision quadrants (`REORDER NOW`, `MARKDOWN / CLEAR`), helping supply chain planners protect bestseller revenues and release working capital.

Check out the full repository and technical report below!

🔗 [Link to GitHub Repository]

#MachineLearning #DataScience #DataEngineering #DemandForecasting #InventoryManagement #SupplyChain #Python #Streamlit #PredictiveAnalytics #DirectToConsumer
