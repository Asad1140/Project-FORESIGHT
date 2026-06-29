# PRESENTATION OUTLINE: PROJECT FORESIGHT
**Demand & Inventory Intelligence for NorthBay Living**

This document outlines a 10-slide professional presentation designed for leadership, stakeholders, and technical recruiters. Each slide includes the slide title, proposed visual elements, key bullet points, and detailed speaker notes.

---

### Slide 1: Title Slide
*   **Slide Title**: Project FORESIGHT: Demand & Inventory Intelligence
*   **Subtitle**: Machine Learning Forecasting & Early-Warning Risk Management for Direct-to-Consumer (DTC) Retail
*   **Visuals**: Premium dark background with a high-contrast glowing indigo-violet abstract network diagram.
*   **Slide Content**:
    *   Developed for: NorthBay Living Analytics Group
    *   Presented by: Machine Learning & Supply Chain Engineering Team
    *   Core Focus: 6-Week Demand Forecasting & Reorder Optimization
*   **Speaker Notes**:
    > "Welcome, everyone. Today I am excited to present Project FORESIGHT, a decision-intelligence system designed for NorthBay Living. DTC retail brands operate in a high-velocity environment where supply chain precision determines profitability. Project FORESIGHT replaces traditional intuition-based inventory planning with a production-ready machine learning pipeline that forecasts weekly demand and mitigates inventory risks before they impact the bottom line."

---

### Slide 2: The Business Challenge
*   **Slide Title**: The Cost of Inventory Mismanagement
*   **Visuals**: A split screen showing two sides of a scale: a dry warehouse shelf labeled "Stockouts" on the left, and boxes piled high labeled "Excess Capital" on the right.
*   **Slide Content**:
    *   **The Stockout Dilemma**: Lost revenue on bestsellers due to unexpected demand spikes.
    *   **The Overstock Burden**: Working capital locked up in slow-moving items, compounding holding fees.
    *   **The Manual Inefficiency**: Replenishment schedules managed on manual, error-prone spreadsheets.
*   **Speaker Notes**:
    > "Like many growing retail brands, NorthBay Living faced two major inventory challenges. First, popular products frequently went out of stock, leading to lost sales and disappointed customers. Second, slow-moving items locked up capital in warehouses. Without an automated, data-driven system, supply chain managers had to rely on intuition and spreadsheets, which failed to scale as the catalog grew."

---

### Slide 3: Project Objectives
*   **Slide Title**: Objectives & Key Deliverables
*   **Visuals**: Four circular icons arranged in a grid, representing Forecast, Risk, Action, and Impact.
*   **Slide Content**:
    *   **Demand Forecasting**: Weekly SKU-level forecasts over a 6-week forward-looking horizon.
    *   **Multi-Factor Risk Engine**: Automated Stockout and Overstock risk scoring.
    *   **Actionable Decisions**: Categorization of SKUs into replenishment quadrants.
    *   **Financial Impact**: Quantified Rupees at risk and capital locked in excess inventory.
*   **Speaker Notes**:
    > "To address these challenges, we established four clear goals. First, build a weekly forecasting model with a 6-week horizon. Second, score each SKU on stockout and overstock risk factors. Third, group SKUs into four actionable quadrants—Healthy, Reorder, Markdown, or Watch—so operators know exactly what actions to take. Finally, translate these risks into concrete financial impacts in Rupees, helping leadership prioritize their focus."

---

### Slide 4: Data Integration & Cleaning
*   **Slide Title**: Establishing a Single Source of Truth
*   **Visuals**: Ingestion flow chart showing four raw datasets (Sales, SKU master, Calendar, Inventory) feeding into an automated cleaning block, outputting clean files.
*   **Slide Content**:
    *   **Clean Datasets**: Integrated sales transactions, SKU metadata, calendar event timelines, and inventory snapshots.
    *   **Automated Audit checks**: Deduplication, datatype verification, and referential integrity.
    *   **Revenue Consistency Check**: Automated correction of mismatched sales records.
    *   **IQR Outlier Capping**: Capping extreme promotional spikes (3x IQR) to prevent forecast distortion.
*   **Speaker Notes**:
    > "A machine learning model is only as good as the data it trains on. Our pipeline integrates four datasets, aligning daily transactions with calendar events and SKU metadata. The automated cleaning module handles deduplication, type checks, and referential integrity. Crucially, we enforce a revenue consistency check and apply a 3x IQR outlier capping mechanism to sales spikes, ensuring that abnormal sales promotions don't distort our baseline demand forecast."

---

### Slide 5: Advanced Feature Engineering
*   **Slide Title**: Extracting Time-Series Signals
*   **Visuals**: Table grouping the 15 engineered features into Lags, Rolling stats, Calendar, and Flags.
*   **Slide Content**:
    *   **Lags**: Lags 1, 7, 14, 28 (days ago) to capture short-term and weekly historical demand.
    *   **Rolling Statistics**: Rolling Mean, Std, Max, and Min (7-day window, shifted by 1 day to prevent leakage).
    *   **Calendar Components**: Day of Week, Week Number, Month, Quarter.
    *   **Indicators**: Holiday Flag, Promotion Flag, Weekend Flag.
*   **Speaker Notes**:
    > "To help our model capture complex demand patterns, we engineered 15 features on a daily level. These include historical lags and rolling window statistics to capture momentum, along with calendar features. Crucially, rolling features are computed on lagged data (shifted by 1 day) to avoid look-ahead leakage. By aggregating these features weekly, our daily lags map to weekly lags, capturing historical demand curves."

---

### Slide 6: Machine Learning Forecasting Model
*   **Slide Title**: Recursive Multi-Step Random Forest
*   **Visuals**: Diagram illustrating the recursive forecasting loop. Pred $t+1$ is used to compute lags for predicting $t+2$, and so on.
*   **Slide Content**:
    *   **Algorithm**: Random Forest Regressor (100 estimators) trained on weekly demand.
    *   **TimeSeriesSplit CV**: 5-fold chronological validation to prevent temporal leakage.
    *   **Recursive Forecasting**: Iterative 6-week future predictions, propagating predictions back as lagged inputs.
    *   **Confidence Bands**: standard errors scaled by $\sqrt{\text{step}}$ to calculate 80% confidence intervals.
*   **Speaker Notes**:
    > "At the core of Project FORESIGHT is a Random Forest Regressor trained on weekly aggregated SKU demand. To evaluate performance, we used a 5-fold TimeSeriesSplit, ensuring that the model is only tested on future data. Our 6-week forecast runs recursively, meaning predictions are fed back as inputs for subsequent steps. To communicate uncertainty to operators, we scale the training residuals by the square root of the step, providing a realistic 80% confidence interval."

---

### Slide 7: Evaluation & Model Comparison
*   **Slide Title**: Outperforming the Seasonal-Naive Baseline
*   **Visuals**: Bar chart showing WAPE comparison between the Seasonal-Naive Baseline and Random Forest model, followed by a metrics table.
*   **Slide Content**:
    *   **WAPE Improvement**: **9.86% WAPE** for ML model vs. **23.46%** for the baseline (**+13.60% improvement**).
    *   **Error Reduction**: Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) are halved.
    *   **Balanced Predictions**: Near-zero forecast bias (**+0.33%**), indicating unbiased predictions.
*   **Speaker Notes**:
    > "We compared our Random Forest model against a Seasonal-Naive baseline, which simply projects sales from the same week in the previous year. On our backtest period, the ML model achieved a WAPE of 9.86%, outperforming the baseline by 13.60%. By halving the error magnitude and keeping forecast bias near zero, the model provides highly accurate, balanced demand predictions."

---

### Slide 8: The Supply Chain Decision Dashboard
*   **Slide Title**: Interactive Inventory Intelligence
*   **Visuals**: Interface mockups showing the Risk Matrix Scatter Grid, Priority Tables, and the SKU Deep Dive Panel.
*   **Slide Content**:
    *   **Executive Board**: Interactive Plotly stockout vs. overstock risk grid.
    *   **Replenishment priority**: Action tables highlighting critical reorders and excess capital.
    *   **SKU Deep Dive**: Historical sales vs. forecasts with confidence bands and inventory gauges.
    *   **Fast cached Loader**: Service layer optimized to load pre-cleaned CSVs instantly.
*   **Speaker Notes**:
    > "We wrapped this pipeline in an interactive Streamlit dashboard. The Executive Board plots every SKU on a risk matrix, where bubble size reflects the financial value at stake. Prioritized action tables show operators exactly what to reorder or markdown. A deep dive tab displays historical sales alongside forecasts and confidence bands, helping planners inspect individual products. We also optimized the database loader to load pre-cleaned files directly, ensuring the dashboard loads instantly."

---

### Slide 9: Business & Financial Impact
*   **Slide Title**: Delivering Concrete Value
*   **Visuals**: Icons representing Revenue Protection, Capital Efficiency, and Operational Efficiency.
*   **Slide Content**:
    *   **Revenue Protection**: Identifies stockout deficits early, preventing lost bestseller sales.
    *   **Working Capital Release**: Identifies overstock holdings, recommending promotional markdowns.
    *   **Operational Efficiency**: Replaces manual spreadsheets with automated ordering recommendations.
*   **Speaker Notes**:
    > "Project FORESIGHT delivers measurable business value. By flagging stockout risks early, it helps secure bestseller revenue. By identifying overstocked inventory, it helps release working capital through targeted promotions. Finally, it streamlines the inventory planning workflow, shifting planners from manual data entry to strategic decision-making."

---

### Slide 10: Future Roadmap & Limitations
*   **Slide Title**: Looking Ahead: Roadmap & Next Steps
*   **Visuals**: A horizontal timeline showing the future development phases.
*   **Slide Content**:
    *   **Cold Start Handling**: Improving forecasts for new SKUs with less than 28 days of history.
    *   **Dynamic Logistics**: Integrating carrier and customs APIs to update lead times in real time.
    *   **User Promo Inputs**: Allowing planners to input planned promotions directly into the UI.
    *   **Deep Learning Sequence Models**: Testing sequence-to-sequence networks for sparse demand.
*   **Speaker Notes**:
    > "While the current system is highly effective, we have identified a roadmap for future expansion. We plan to improve handling for new products without sales history, integrate logistics APIs for dynamic lead times, and allow planners to input planned promo schedules directly. We also plan to evaluate deep learning sequence models like Temporal Fusion Transformers to better handle sparse demand. Thank you for your time, and I am happy to take any questions."
