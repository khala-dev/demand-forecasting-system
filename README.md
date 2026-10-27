# Retail Demand Forecasting & Profitability System

An end-to-end data engineering, financial diagnostics, and machine learning forecasting pipeline built with PostgreSQL, Python, scikit-learn, and Streamlit.

## Overview

Retail operations frequently suffer from two competing inefficiencies: inventory stockouts/overstocking due to inaccurate demand planning, and margin erosion caused by uncalibrated promotional discounting. This system integrates a relational star-schema database with an automated ETL pipeline, SQL analytical views, and a gradient boosting time-series model to optimize stock allocation and evaluate promotion profitability.

## System Architecture

```text
demand-forecasting-system/
├── sql/
│   ├── schema.sql           # Star schema DDL (stores, products, daily_sales)
│   └── analyticsView.sql    # Pre-aggregated financial view (sales_analytics_view)
├── src/
│   ├── database.py          # SQLAlchemy connection engine & environment config
│   ├── pipeline.py          # Synthetic time-series ETL generator (10,965 records)
│   ├── analytics.py         # Store performance & promotion margin diagnostics
│   ├── forecasting.py       # Lag/rolling feature engineering & HistGradientBoosting model
│   └── app.py               # Interactive BI & decision simulation dashboard (Streamlit/Plotly)
└── requirements.txt         # Project dependencies