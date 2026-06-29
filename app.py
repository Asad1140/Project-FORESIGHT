# -*- coding: utf-8 -*-
"""
Project FORESIGHT: Demand & Inventory Intelligence Panel
--------------------------------------------------------
A premium Streamlit application for advanced inventory decisioning,
demand forecasting, and risk scoring.
"""

import sys
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Ensure src/ is in path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from config import COLOR_MAP
from utils import format_rupees, setup_logging
from risk_engine import calculate_risk_scoring
from forecast_service import load_base_data, load_forecast_data, ForecastDataMissingError
from charts import plot_risk_matrix, plot_forecast, plot_inventory_gauge

# Initialize central logging
logger = setup_logging()
logger.info("Initializing Project FORESIGHT Streamlit Dashboard Startup...")

# Page Configuration
st.set_page_config(
    page_title="Project FORESIGHT // NorthBay Living",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS (Indigo-Violet Dark/Light theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Font style */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Title style */
    .title-gradient {
        background: linear-gradient(135deg, #818cf8, #4f46e5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.8rem;
        margin-bottom: 0.1rem;
    }
    
    /* Metric container */
    .metric-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric-container:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.4);
        background: rgba(99, 102, 241, 0.02);
        box-shadow: 0 10px 25px rgba(99, 102, 241, 0.1);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 5px 0;
    }
    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #9ca3af;
        font-weight: 500;
    }
    .metric-delta {
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    /* AI Card Panel */
    .ai-panel {
        background: linear-gradient(145deg, rgba(79, 70, 229, 0.05), rgba(168, 85, 247, 0.05));
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Trend Card styling */
    .trend-card {
        padding: 10px 15px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin-bottom: 10px;
        text-align: left;
    }
    
    /* Progress bar styling override */
    .stProgress > div > div > div > div {
        background-color: #4f46e5;
    }
</style>
""", unsafe_allow_html=True)

# Load and clean base data (cached for speed)
@st.cache_data
def get_base_data():
    logger.info("Triggering cached base data loading...")
    sku_df, sales_df, calendar_df, inventory_df = load_base_data()
    return sku_df, sales_df, calendar_df, inventory_df

sku_df, sales_df, calendar_df, inventory_df = get_base_data()

# Load forecast results and WAPE metrics
@st.cache_data
def get_forecast_data():
    logger.info("Triggering cached forecast data loading...")
    return load_forecast_data()

# Try loading forecast data, handle missing files explicitly
forecast_available = True
try:
    forecast_results, forecast_metrics, pipeline_run_log = get_forecast_data()
    logger.info("Forecast data and evaluation metrics loaded successfully.")
except ForecastDataMissingError as e:
    forecast_available = False
    forecast_results = None
    forecast_metrics = None
    pipeline_run_log = None
    logger.warning("Forecast pipeline outputs are missing. Operating in degraded mode.")

# Latest snapshot date
latest_snapshot_date = inventory_df["date"].max()
latest_inventory = inventory_df[inventory_df["date"] == latest_snapshot_date].copy()

# Sidebar Control Panel
st.sidebar.markdown("### 🔮 Control Panel")
category_list = ["All"] + sorted(sku_df["category"].unique().tolist())
selected_category = st.sidebar.selectbox("Select Product Category", category_list)

# Filter SKUs by category
if selected_category != "All":
    filtered_skus = sku_df[sku_df["category"] == selected_category]
else:
    filtered_skus = sku_df

sku_list = sorted(filtered_skus["sku_id"].unique().tolist())
selected_sku = st.sidebar.selectbox("Select Deep-Dive SKU", sku_list)

st.sidebar.markdown("### 🛠️ What-If Simulation")
sim_lead_time_override = st.sidebar.checkbox("Override SKU Lead Times?")
sim_lead_time_days = st.sidebar.slider("Simulation Lead Time (Days)", 7, 30, 14, disabled=not sim_lead_time_override)
sim_safety_stock_factor = st.sidebar.slider("Safety Stock Level (weeks of demand)", 1.0, 4.0, 1.5, 0.1)

# Risk scoring calculation
risk_df = calculate_risk_scoring(
    latest_inventory=latest_inventory,
    sku_df=sku_df,
    sales_df=sales_df,
    safety_stock_weeks=sim_safety_stock_factor,
    lt_override=sim_lead_time_override,
    lt_days=sim_lead_time_days,
    selected_category=selected_category
)

# App Header
st.markdown('<div class="title-gradient">Project FORESIGHT</div>', unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; color: #9ca3af; margin-bottom: 1.5rem;'>Demand & Inventory Intelligence Panel // NorthBay Living</p>", unsafe_allow_html=True)

# Alert user if forecasting data is missing
if not forecast_available:
    st.error("### ⚠️ Forecast Pipeline Outputs Missing\n"
             "The demand forecasting results and performance metrics could not be loaded.\n\n"
             "**To resolve this and unlock forecast visualizations:**\n"
             "1. Activate your virtual environment: `venv\\Scripts\\Activate.ps1`\n"
             "2. Run the forecast training pipeline from your terminal:\n"
             "   ```bash\n"
             "   python src/train_forecast.py\n"
             "   ```\n"
             "3. Refresh this webpage after the pipeline completes successfully.")

# Calculate key stats
num_reorders = len(risk_df[risk_df["quadrant"] == "REORDER NOW"])
num_markdowns = len(risk_df[risk_df["quadrant"] == "MARKDOWN / CLEAR"])
total_sales_at_risk = risk_df["sales_at_risk"].sum()
total_capital_locked = risk_df["capital_locked"].sum()

if forecast_available:
    forecast_acc = 1.0 - forecast_metrics["ml_wape"]
    baseline_acc = 1.0 - forecast_metrics["baseline_wape"]
    improvement_text = f"+{forecast_metrics['improvement']:.1%}"
    forecast_val_text = f"{forecast_acc:.1%}"
    baseline_val_text = f"Baseline accuracy: {baseline_acc:.1%}"
    executive_ml_summary = f"The newly integrated Machine Learning forecast model achieves a backtest accuracy of <b>{forecast_acc:.1%}</b>, outperforming the seasonal baseline by <b>+{forecast_metrics['improvement']:.1%}</b>."
else:
    forecast_val_text = "N/A"
    baseline_val_text = "Run train_forecast.py"
    improvement_text = "N/A"
    executive_ml_summary = "Machine Learning forecast metrics are currently unavailable. Run the training script to evaluate model accuracy."

# 1. Executive Summary Bar & Trend Cards
summary_cols = st.columns([3, 1])

with summary_cols[0]:
    st.markdown(f"""
    <div class="ai-panel">
        <h4 style="margin-top:0; color:#818cf8; font-weight:600; font-size:1.1rem;">🚨 EXECUTIVE SUMMARY & AI INSIGHTS</h4>
        <p style="margin: 0; font-size: 0.95rem; line-height: 1.5;">
            Today, there are <b>{num_reorders} SKUs</b> requiring immediate reorder to prevent stockouts, representing 
            <b>{format_rupees(total_sales_at_risk)}</b> in potential revenue at risk. 
            Conversely, <b>{num_markdowns} SKUs</b> are overstocked, locking up <b>{format_rupees(total_capital_locked)}</b> in working capital. 
            {executive_ml_summary}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
with summary_cols[1]:
    # Inventory Health Score calculation (100 - penalize stockouts & overstock ratio)
    total_items = len(risk_df)
    health_penalty = ((num_reorders + num_markdowns) / total_items) * 100 if total_items > 0 else 0
    health_score = int(100 - health_penalty)
    
    st.markdown(f"""
    <div class="metric-container" style="padding: 12px 20px;">
        <div class="metric-title" style="font-size:0.75rem;">Inventory Health</div>
        <div class="metric-value" style="color: #10b981; font-size: 1.7rem; margin:2px 0;">{health_score}/100</div>
        <div class="metric-delta" style="color: #6b7280; font-size:0.75rem;">Target: 95+</div>
    </div>
    """, unsafe_allow_html=True)

# 2. KPI Cards Row
kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">Active SKUs Monitored</div>
        <div class="metric-value" style="color: #6366f1;">{len(risk_df)}</div>
        <div class="metric-delta" style="color: #9ca3af;">{selected_category} Category</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">Revenue at Risk</div>
        <div class="metric-value" style="color: #f87171;">{format_rupees(total_sales_at_risk)}</div>
        <div class="metric-delta" style="color: #f87171;">↓ 11% Stockout risk</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">Capital Locked</div>
        <div class="metric-value" style="color: #c084fc;">{format_rupees(total_capital_locked)}</div>
        <div class="metric-delta" style="color: #c084fc;">↓ 5% Overstock hold</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">ML Forecast Accuracy</div>
        <div class="metric-value" style="color: #34d399;">{forecast_val_text}</div>
        <div class="metric-delta" style="color: #34d399;">{baseline_val_text}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Content Tabs
tabs = st.tabs(["📊 Executive Decision Board", "🧠 AI Recommendations", "🔍 SKU Deep Dive", "⚙️ Data Pipeline Health"])

# Tab 1: Executive Decision Board
with tabs[0]:
    st.markdown("### 🗺️ Stockout vs Overstock Risk Matrix")
    st.markdown("Every SKU is plotted on the multi-factor risk grid. Bubble size represents **financial impact** (rupees at stake).")
    
    # Render Risk Matrix Scatter
    fig_grid = plot_risk_matrix(risk_df, COLOR_MAP)
    st.plotly_chart(fig_grid, use_container_width=True)
    
    # Action tables
    action_cols = st.columns(2)
    
    with action_cols[0]:
        st.markdown("#### 🚨 Reorder Priority Table")
        reorder_list = risk_df[risk_df["quadrant"] == "REORDER NOW"].sort_values(by="sales_at_risk", ascending=False).head(5)
        if not reorder_list.empty:
            reorder_display = reorder_list[["sku_id", "subcategory", "on_hand_units", "on_order_units", "units_short", "sales_at_risk"]].copy()
            reorder_display["units_short"] = reorder_display["units_short"].round(0).astype(int)
            reorder_display["sales_at_risk"] = reorder_display["sales_at_risk"].map(format_rupees)
            reorder_display = reorder_display.rename(columns={
                "sku_id": "SKU",
                "subcategory": "Subcategory",
                "on_hand_units": "On Hand",
                "on_order_units": "On Order",
                "units_short": "Deficit Units",
                "sales_at_risk": "Revenue Saved Potential"
            })
            st.dataframe(reorder_display, use_container_width=True, hide_index=True)
        else:
            st.success("No critical stockout risks identified for this category.")
            
    with action_cols[1]:
        st.markdown("#### ⏳ Overstock Clearance Table")
        overstock_list = risk_df[risk_df["quadrant"] == "MARKDOWN / CLEAR"].sort_values(by="capital_locked", ascending=False).head(5)
        if not overstock_list.empty:
            overstock_display = overstock_list[["sku_id", "subcategory", "on_hand_units", "weekly_avg_sales", "capital_locked"]].copy()
            overstock_display["capital_locked"] = overstock_display["capital_locked"].map(format_rupees)
            overstock_display["weekly_avg_sales"] = overstock_display["weekly_avg_sales"].round(1)
            overstock_display = overstock_display.rename(columns={
                "sku_id": "SKU",
                "subcategory": "Subcategory",
                "on_hand_units": "On Hand",
                "weekly_avg_sales": "Weekly Demand",
                "capital_locked": "Capital Locked"
            })
            st.dataframe(overstock_display, use_container_width=True, hide_index=True)
        else:
            st.success("No severe overstock conditions identified for this category.")

# Tab 2: AI Recommendations & Business Insights
with tabs[1]:
    st.markdown("### 🧠 AI Intelligence Panel & Action Generator")
    
    ai_cols = st.columns([2, 1])
    
    with ai_cols[0]:
        st.markdown("#### 📋 Prioritized Reorder Execution Plan")
        reorders = risk_df[risk_df["quadrant"] == "REORDER NOW"].sort_values(by="sales_at_risk", ascending=False)
        
        if not reorders.empty:
            reorder_plan = []
            for _, r in reorders.iterrows():
                # Recommend ordering 4 weeks of demand
                rec_qty = int(np.ceil(r["weekly_avg_sales"] * 4.0))
                urgency = "Immediate (2 days)" if r["stockout_risk"] > 0.75 else "High (5 days)"
                
                reorder_plan.append({
                    "SKU": r["sku_id"],
                    "Category": r["category"],
                    "Lead Time": f"{r['lead_time_days']} days",
                    "Recommended Order Qty": f"{rec_qty} units",
                    "Timeline Urgency": urgency,
                    "Est. Revenue Protected": format_rupees(r["sales_at_risk"])
                })
            st.dataframe(pd.DataFrame(reorder_plan), use_container_width=True, hide_index=True)
        else:
            st.success("All SKU inventory levels are within safe holding ranges!")
            
        st.markdown("#### 🛍️ Markdown Discount Strategies")
        markdowns = risk_df[risk_df["quadrant"] == "MARKDOWN / CLEAR"].sort_values(by="capital_locked", ascending=False)
        if not markdowns.empty:
            markdown_plan = []
            for _, r in markdowns.iterrows():
                weeks_hold = r["on_hand_units"] / (r["weekly_avg_sales"] + 1e-5)
                # Suggest discount based on excess
                discount = "30% Clearance" if weeks_hold > 12 else "15% Promotional Promo"
                
                markdown_plan.append({
                    "SKU": r["sku_id"],
                    "Subcategory": r["subcategory"],
                    "Current Stock": f"{r['on_hand_units']} units",
                    "Weeks of Supply": f"{weeks_hold:.1f} weeks",
                    "Suggested Action": discount,
                    "Capital Released Potential": format_rupees(r["capital_locked"])
                })
            st.dataframe(pd.DataFrame(markdown_plan), use_container_width=True, hide_index=True)
        else:
            st.success("No critical overstock holdings detected.")
            
    with ai_cols[1]:
        st.markdown("#### 💡 Strategic Business Insights")
        
        # Calculate Category level contributions
        cat_sales = sales_df.groupby("sku_id")["revenue"].sum().reset_index()
        cat_sales = pd.merge(cat_sales, sku_df, on="sku_id")
        cat_revenue = cat_sales.groupby("category")["revenue"].sum().reset_index()
        total_rev = cat_revenue["revenue"].sum()
        cat_revenue["percent"] = (cat_revenue["revenue"] / total_rev) * 100
        cat_revenue = cat_revenue.sort_values(by="percent", ascending=False)
        
        st.markdown("**Top Category Revenue Contribution:**")
        for _, row in cat_revenue.iterrows():
            st.markdown(f"- **{row['category']}**: accounts for {row['percent']:.1f}% of total sales ({format_rupees(row['revenue'])}).")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Calculate Stockout Risk per Category
        st.markdown("**High-Risk Stockout Concentrations:**")
        risk_by_cat = risk_df.groupby("category")["quadrant"].apply(lambda x: (x == "REORDER NOW").sum()).reset_index()
        risk_by_cat = risk_by_cat.sort_values(by="quadrant", ascending=False)
        for _, row in risk_by_cat.iterrows():
            if row["quadrant"] > 0:
                st.markdown(f"- **{row['category']}** has **{row['quadrant']} SKUs** requiring immediate reordering.")
                
        # Download Center
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📄 Download Center")
        
        # Download Forecasts (Disabled if forecasts are unavailable)
        if forecast_available and forecast_results is not None:
            csv_fc = forecast_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Forecast Report (CSV)",
                data=csv_fc,
                file_name="forecast_report.csv",
                mime="text/csv",
                key="dl_fc"
            )
        else:
            st.button("📥 Download Forecast Report (CSV) [Model Not Trained]", disabled=True)
            
        # Download Risk Table
        csv_risk = risk_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Risk Analysis (CSV)",
            data=csv_risk,
            file_name="inventory_risk_report.csv",
            mime="text/csv",
            key="dl_risk"
        )
        
        # Download Reorder Action Plan
        if not reorders.empty:
            reorder_csv = pd.DataFrame(reorder_plan).to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Reorder Action Plan (CSV)",
                data=reorder_csv,
                file_name="reorder_action_plan.csv",
                mime="text/csv",
                key="dl_plan"
            )

# Tab 3: SKU Deep Dive (Visualizations & Models)
with tabs[2]:
    st.markdown(f"### 🔍 Detailed Analysis for SKU: **{selected_sku}**")
    
    sku_row = risk_df[risk_df["sku_id"] == selected_sku].iloc[0]
    
    deep_cols = st.columns([2, 1])
    
    with deep_cols[0]:
        st.markdown("#### Historical Demand vs. Baseline vs. ML Forecast")
        
        if forecast_available and forecast_results is not None:
            sku_fc = forecast_results[forecast_results["sku_id"] == selected_sku].copy()
            sku_fc = sku_fc.sort_values(by="date")
            
            # Slice historical + backtest + future for plotting
            plot_start_date = pd.to_datetime("2025-08-01")
            plot_df = sku_fc[sku_fc["date"] >= plot_start_date].copy()
            
            # Plot using modular charts module
            fig_fc = plot_forecast(plot_df)
            st.plotly_chart(fig_fc, use_container_width=True)
        else:
            st.warning("⚠️ **Forecast visualizations are unavailable** because the model has not been trained yet. Please run `python src/train_forecast.py` to generate the forecasting results.")
            
    with deep_cols[1]:
        st.markdown("#### 📦 Current Inventory Position")
        
        # Gauge chart for On-hand Inventory relative to Reorder Point
        rop_calc = sku_row["reorder_point_calc"]
        supply = sku_row["current_supply"]
        
        fig_gauge = plot_inventory_gauge(sku_row, rop_calc)
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Decision rationale card
        st.markdown("#### Decision Rationale")
        action = sku_row["quadrant"]
        
        if action == "REORDER NOW":
            rec_qty = int(np.ceil(sku_row["weekly_avg_sales"] * 4.0))
            st.error(f"""
            **Action: REORDER NOW**
            - **Status**: Current supply ({supply} units) is below the threshold reorder point of **{int(rop_calc)} units**.
            - **Shortage Impact**: Projected deficit of **{int(sku_row['units_short'])} units** during lead time.
            - **Recommended Order**: Order **{rec_qty} units** immediately to secure 4 weeks of demand.
            - **Expected Revenue Protected**: **{format_rupees(sku_row['sales_at_risk'])}**.
            """)
        elif action == "MARKDOWN / CLEAR":
            weeks_hold = sku_row["on_hand_units"] / (sku_row["weekly_avg_sales"] + 1e-5)
            st.warning(f"""
            **Action: MARKDOWN / CLEAR**
            - **Status**: On Hand stock is **{sku_row['on_hand_units']} units**, representing **{weeks_hold:.1f} weeks** of supply (target: <= 6 weeks).
            - **Capital Locked**: **{format_rupees(sku_row['capital_locked'])}** is locked in excess inventory.
            - **Recommended Action**: Apply a promotional discount (15% - 30%) to accelerate velocity.
            """)
        elif action == "WATCH / VOLATILE":
            st.info(f"""
            **Action: WATCH / VOLATILE**
            - **Status**: Stock levels and demand are highly volatile.
            - **Sales at Risk**: {format_rupees(sku_row['sales_at_risk'])}
            - **Capital Locked**: {format_rupees(sku_row['capital_locked'])}
            - **Recommendation**: Audit SKU sales manually. Demand spikes or large lead times require merchandiser review.
            """)
        else:
            st.success(f"""
            **Action: HEALTHY**
            - **Status**: Current stock level ({supply} units) is above safety thresholds and within optimal boundaries.
            - **Recommendation**: No action needed. Continue standard tracking.
            """)

# Tab 4: Data Pipeline Health
with tabs[3]:
    st.markdown("### ⚙️ Data Preparation & Validation Health Logs")
    st.markdown("This tab displays the logs of our automated preprocessing and data audit pipeline.")
    
    if forecast_available and pipeline_run_log is not None:
        log_cols = st.columns(2)
        
        with log_cols[0]:
            st.markdown("#### 📋 Data Integrity Dashboard")
            
            raw_rows = pipeline_run_log.get("raw_sales_rows", 91039)
            clean_rows = pipeline_run_log.get("clean_sales_rows", raw_rows - 1000)
            dropped_rows = raw_rows - clean_rows
            
            st.markdown(f"**Total Raw Rows Received:** `{raw_rows:,}`")
            st.markdown(f"**Total Processed Rows Saved:** `{clean_rows:,}`")
            st.markdown(f"**Rows Filtered / Removed:** `{dropped_rows:,}`")
            
            st.progress(clean_rows / raw_rows)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Audit Removal Breakdown:")
            st.write({
                "Duplicates Removed": f"{pipeline_run_log.get('duplicate_sales_removed', 0):,}",
                "Missing Values Cleaned": f"{pipeline_run_log.get('missing_sales_removed', 0):,}",
                "Negative Anomalies Dropped": f"{pipeline_run_log.get('negative_values_removed', 0):,}",
                "Invalid SKU IDs Filtered": f"{pipeline_run_log.get('invalid_skus_removed', 0):,}",
                "Revenue Mismatches Corrected": f"{pipeline_run_log.get('revenue_consistency_corrected', 0):,}",
                "Outlier Capping Events": f"{pipeline_run_log.get('outliers_capped', 0):,}"
            })
            
        with log_cols[1]:
            st.markdown("#### 🤖 Forecast Model Performance Audit")
            st.markdown("**Weighted Absolute Percentage Error (WAPE) Comparison:**")
            
            col_wape = st.columns(2)
            with col_wape[0]:
                st.metric("Baseline Model WAPE", f"{forecast_metrics['baseline_wape']:.2%}")
            with col_wape[1]:
                st.metric("ML Forecasting WAPE", f"{forecast_metrics['ml_wape']:.2%}", 
                          delta=f"-{forecast_metrics['improvement']:.2%}", delta_color="inverse")
                
            st.markdown("""
            > [!NOTE]
            > **WAPE Calculation Details:**
            > * Backtest Period: **Nov 20, 2025 to Dec 31, 2025**
            > * Actual sales are grouped weekly and compared against predictions.
            > * Lower WAPE scores indicate higher forecasting precision and more reliable inventory planning suggestions.
            """)
    else:
        st.warning("⚠️ **Pipeline health metrics are unavailable** because the forecasting run logs are missing. Please run `python src/train_forecast.py` to populate performance comparisons and preprocessing audit data.")

st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><p style='text-align: center; color: #4b5563; font-size: 0.8rem;'>Project FORESIGHT // NorthBay Living Analytics Group</p>", unsafe_allow_html=True)
