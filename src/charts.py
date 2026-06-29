# -*- coding: utf-8 -*-
"""
Project FORESIGHT: UI Charts Visualization Module
------------------------------------------------
Provides helper functions for generating Plotly figures (Risk Matrix scatter grid,
demand forecasts with confidence bands, and inventory gauge metrics).
"""

import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils import format_rupees

logger = logging.getLogger(__name__)


def plot_risk_matrix(risk_df: pd.DataFrame, color_map: dict) -> go.Figure:
    """
    Renders the Stockout vs. Overstock risk matrix scatter plot with shaded quadrants.

    Args:
        risk_df (pd.DataFrame): Computed risk analysis DataFrame.
        color_map (dict): Hex color mappings for decision quadrants.

    Returns:
        go.Figure: Renders the Plotly scatter figure.
    """
    logger.info("Generating risk matrix scatter plot...")
    fig_grid = go.Figure()
    
    # Background quadrant shading
    # Lower-Left: Healthy (Green)
    fig_grid.add_shape(type="rect", x0=0, y0=0, x1=0.45, y1=0.55,
                       fillcolor="rgba(16, 185, 129, 0.04)", line_width=0, layer="below")
    # Upper-Left: Reorder (Red)
    fig_grid.add_shape(type="rect", x0=0, y0=0.55, x1=0.45, y1=1.0,
                       fillcolor="rgba(239, 68, 68, 0.04)", line_width=0, layer="below")
    # Lower-Right: Markdown (Purple)
    fig_grid.add_shape(type="rect", x0=0.45, y0=0, x1=1.0, y1=0.55,
                       fillcolor="rgba(168, 85, 247, 0.04)", line_width=0, layer="below")
    # Upper-Right: Volatile / Watch (Yellow)
    fig_grid.add_shape(type="rect", x0=0.45, y0=0.55, x1=1.0, y1=1.0,
                       fillcolor="rgba(245, 158, 11, 0.04)", line_width=0, layer="below")
    
    for quad, color in color_map.items():
        quad_data = risk_df[risk_df["quadrant"] == quad]
        if not quad_data.empty:
            fig_grid.add_trace(go.Scatter(
                x=quad_data["overstock_risk"],
                y=quad_data["stockout_risk"],
                mode='markers',
                marker=dict(
                    size=np.maximum(10, np.sqrt(quad_data["sales_at_risk"] + quad_data["capital_locked"]) / 12),
                    color=color,
                    line=dict(width=1, color='rgba(255, 255, 255, 0.5)')
                ),
                name=quad,
                text=quad_data["sku_id"],
                customdata=np.stack((
                    quad_data["category"], 
                    quad_data["on_hand_units"],
                    quad_data["on_order_units"],
                    quad_data["sales_at_risk"].map(format_rupees),
                    quad_data["capital_locked"].map(format_rupees)
                ), axis=-1),
                hovertemplate="<b>SKU: %{text}</b><br>" +
                              "Category: %{customdata[0]}<br>" +
                              "On Hand: %{customdata[1]} | On Order: %{customdata[2]}<br>" +
                              "Sales at Risk: %{customdata[3]}<br>" +
                              "Capital Locked: %{customdata[4]}<br>" +
                              "<extra></extra>"
            ))
            
    fig_grid.update_layout(
        xaxis=dict(title="Overstock Risk (On-hand vs forward sales)", range=[0, 1.05], gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title="Stockout Risk (Multi-factor score)", range=[0, 1.05], gridcolor='rgba(255,255,255,0.05)'),
        height=500,
        margin=dict(l=40, r=40, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig_grid


def plot_forecast(plot_df: pd.DataFrame) -> go.Figure:
    """
    Renders the demand forecasting plot with actual demand, naive baseline, ML forecast,
    and a shaded 80% confidence interval.

    Args:
        plot_df (pd.DataFrame): Dataframe containing date, actual sales, baseline, and ML predictions.

    Returns:
        go.Figure: Renders the Plotly line/area figure.
    """
    logger.info("Generating demand forecast visualization...")
    fig_fc = go.Figure()
    
    # Plot Actual Sales
    fig_fc.add_trace(go.Scatter(
        x=plot_df["date"],
        y=plot_df["actual_sales"],
        mode='lines+markers',
        name='Historical/Actual Weekly Sales',
        line=dict(color='#6366f1', width=2.5),
        connectgaps=True
    ))
    
    # Plot Baseline Forecast
    fig_fc.add_trace(go.Scatter(
        x=plot_df["date"],
        y=plot_df["baseline_forecast"],
        mode='lines',
        name='Seasonal-Naive Baseline',
        line=dict(color='#fbbf24', width=2, dash='dot')
    ))
    
    # Plot ML Forecast (Random Forest)
    fig_fc.add_trace(go.Scatter(
        x=plot_df["date"],
        y=plot_df["ml_forecast"],
        mode='lines+markers',
        name='ML Forecast (Random Forest)',
        line=dict(color='#10b981', width=2.5)
    ))
    
    # Shaded Confidence Interval for ML Forecast
    future_slice = plot_df[plot_df["actual_sales"].isnull()]
    if not future_slice.empty:
        fig_fc.add_trace(go.Scatter(
            x=future_slice["date"].tolist() + future_slice["date"].tolist()[::-1],
            y=future_slice["ml_upper_bound"].tolist() + future_slice["ml_lower_bound"].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(16, 185, 129, 0.1)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=True,
            name='80% Forecast Confidence Interval'
        ))
        
    fig_fc.update_layout(
        xaxis=dict(title="Date", gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title="Weekly Demand (Units)", gridcolor='rgba(255,255,255,0.05)'),
        height=420,
        margin=dict(l=40, r=40, t=10, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig_fc


def plot_inventory_gauge(sku_row: pd.Series, rop_calc: float) -> go.Figure:
    """
    Renders a gauge chart illustrating current on-hand units vs ROP threshold.

    Args:
        sku_row (pd.Series): Row containing selected SKU attributes (on_hand_units).
        rop_calc (float): Calculated reorder point threshold.

    Returns:
        go.Figure: Renders the Plotly gauge figure.
    """
    logger.info(f"Generating inventory position gauge for SKU {sku_row.get('sku_id', 'unknown')}...")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sku_row["on_hand_units"],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "On-Hand Inventory", 'font': {'size': 15}},
        gauge={
            'axis': {'range': [None, max(50, rop_calc * 2)], 'tickwidth': 1},
            'bar': {'color': "#4f46e5"},
            'steps': [
                {'range': [0, rop_calc], 'color': "rgba(239, 68, 68, 0.15)"},
                {'range': [rop_calc, rop_calc * 1.5], 'color': "rgba(16, 185, 129, 0.15)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 3},
                'thickness': 0.75,
                'value': rop_calc
            }
        }
    ))
    
    fig_gauge.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig_gauge
