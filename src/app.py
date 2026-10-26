import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.database import get_db_engine

# 1. إعداد الصفحة على العرض الكامل
st.set_page_config(
    page_title="Retail Demand & Profitability Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. تنسيق CSS احترافي للبطاقات والواجهة الداكنة
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stMetric"] {
            background-color: #161a23;
            border: 1px solid #2b313e;
            padding: 16px 20px;
            border-radius: 8px;
        }
        div[data-testid="stMetricLabel"] > div {
            font-size: 0.85rem;
            color: #9ca3af;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        div[data-testid="stMetricValue"] > div {
            font-size: 1.65rem;
            font-weight: 700;
            color: #f3f4f6;
        }
        .section-header {
            font-size: 1.15rem;
            font-weight: 600;
            color: #e5e7eb;
            margin-top: 1.2rem;
            margin-bottom: 0.8rem;
            border-left: 3px solid #3b82f6;
            padding-left: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_dashboard_data():
    engine = get_db_engine()

    analytics_query = """
    SELECT 
        sale_date, store_id, store_name, city, store_type,
        product_id, product_name, category, units_sold,
        unit_cost, base_price, selling_price, is_promotion,
        temperature_c, revenue, total_cost, net_profit
    FROM seles_analytics_view
    ORDER BY sale_date;
    """
    df_sales = pd.read_sql(analytics_query, engine)
    df_sales["sale_date"] = pd.to_datetime(df_sales["sale_date"])

    forecast_query = """
    SELECT 
        sale_date, store_name, product_name,
        units_sold, predicted_units, selling_price, is_promotion
    FROM demand_forecasts
    ORDER BY sale_date;
    """
    df_forecast = pd.read_sql(forecast_query, engine)
    df_forecast["sale_date"] = pd.to_datetime(df_forecast["sale_date"])

    return df_sales, df_forecast


def build_forecast_chart(df_fc):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_fc["sale_date"],
            y=df_fc["units_sold"],
            mode="lines+markers",
            name="Actual Demand",
            line=dict(color="#3b82f6", width=2.2),
            marker=dict(size=4),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_fc["sale_date"],
            y=df_fc["predicted_units"],
            mode="lines+markers",
            name="ML Predicted Demand",
            line=dict(color="#f59e0b", width=2.2, dash="dot"),
            marker=dict(size=4),
        )
    )

    fig.update_layout(
        title="Daily Demand Forecast vs. Actuals (Test Period: Nov - Dec 2025)",
        xaxis_title="Date",
        yaxis_title="Units Sold",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#11141c",
        height=390,
        margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    return fig


def build_promo_comparison_chart(df_sl):
    normal_df = df_sl[~df_sl["is_promotion"]]
    promo_df = df_sl[df_sl["is_promotion"]]

    rev_normal = normal_df["revenue"].mean()
    rev_promo = promo_df["revenue"].mean()
    prof_normal = normal_df["net_profit"].mean()
    prof_promo = promo_df["net_profit"].mean()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Regular Days (No Promo)",
            x=["Avg Daily Revenue", "Avg Daily Net Profit"],
            y=[rev_normal, prof_normal],
            marker_color="#4b5563",
            text=[f"${rev_normal:,.2f}", f"${prof_normal:,.2f}"],
            textposition="auto",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Promotion Days (20% Off)",
            x=["Avg Daily Revenue", "Avg Daily Net Profit"],
            y=[rev_promo, prof_promo],
            marker_color="#10b981" if prof_promo >= prof_normal else "#ef4444",
            text=[f"${rev_promo:,.2f}", f"${prof_promo:,.2f}"],
            textposition="auto",
        )
    )

    fig.update_layout(
        title="Promotion Financial Diagnostics (Daily Average)",
        yaxis_title="USD ($)",
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#11141c",
        height=390,
        margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def main():
    df_sales, df_forecast = load_dashboard_data()

    # الشريط الجانبي للتصفية ومعلومات النظام
    st.sidebar.markdown("### System Controls")
    store_list = sorted(df_sales["store_name"].unique())
    selected_store = st.sidebar.selectbox("Store Location", store_list)

    product_list = sorted(df_sales["product_name"].unique())
    selected_product = st.sidebar.selectbox("Product SKU", product_list)

    st.sidebar.divider()
    st.sidebar.markdown("### Date Range Filter")
    min_date = df_sales["sale_date"].min().date()
    max_date = df_sales["sale_date"].max().date()
    start_date, end_date = st.sidebar.date_input(
        "Historical Analysis Window",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # تصفية البيانات حسب اختيار المستعمل
    mask_sales = (
        (df_sales["store_name"] == selected_store)
        & (df_sales["product_name"] == selected_product)
        & (df_sales["sale_date"].dt.date >= start_date)
        & (df_sales["sale_date"].dt.date <= end_date)
    )
    filtered_sales = df_sales[mask_sales].copy()

    filtered_forecast = df_forecast[
        (df_forecast["store_name"] == selected_store)
        & (df_forecast["product_name"] == selected_product)
    ].copy()

    # العنوان الرئيسي ومعلومات المتجر والمنتج المختار
    store_type = filtered_sales["store_type"].iloc[0]
    category = filtered_sales["category"].iloc[0]
    unit_cost = float(filtered_sales["unit_cost"].iloc[0])
    base_price = float(filtered_sales["base_price"].iloc[0])

    st.title("Retail Demand & Profitability Intelligence")
    st.caption(
        f"Store: {selected_store} ({store_type})  |  Product: {selected_product} ({category})  |  "
        f"Base Price: ${base_price:.2f}  |  Unit Cost: ${unit_cost:.2f}"
    )

    # 1. حساب وعرض المؤشرات التنفيذية الخمسة (KPI Cards)
    total_rev = filtered_sales["revenue"].sum()
    total_prof = filtered_sales["net_profit"].sum()
    margin_pct = (total_prof / total_rev * 100) if total_rev > 0 else 0.0

    prof_no_promo = filtered_sales[~filtered_sales["is_promotion"]]["net_profit"].mean()
    prof_with_promo = filtered_sales[filtered_sales["is_promotion"]]["net_profit"].mean()
    promo_diff = prof_with_promo - prof_no_promo

    fc_actual_sum = int(filtered_forecast["units_sold"].sum())
    fc_pred_sum = int(filtered_forecast["predicted_units"].sum())
    fc_mae = np.abs(filtered_forecast["units_sold"] - filtered_forecast["predicted_units"]).mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Revenue", f"${total_rev:,.0f}", f"{int(filtered_sales['units_sold'].sum()):,} units sold")
    col2.metric("Net Profit", f"${total_prof:,.0f}", f"{margin_pct:.1f}% margin")
    col3.metric(
        "Promo Daily Profit Impact",
        f"${prof_with_promo:,.2f}",
        f"{promo_diff:+.2f} USD vs regular",
    )
    col4.metric(
        "60-Day Forecast Stock",
        f"{fc_pred_sum:,} units",
        f"{fc_pred_sum - fc_actual_sum:+d} vs actual ({fc_actual_sum:,})",
    )
    col5.metric("Model MAE (Test)", f"{fc_mae:.2f} units/day", "HistGradientBoosting")

    # 2. قسم الرسوم البيانية التفاعلية (التنبؤ بالطلب + تشخيص التخفيضات)
    st.markdown('<div class="section-header">Demand Forecasting & Promotion Diagnostics</div>', unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns([1.65, 1.0])

    with chart_col1:
        st.plotly_chart(build_forecast_chart(filtered_forecast), use_container_width=True)

    with chart_col2:
        st.plotly_chart(build_promo_comparison_chart(filtered_sales), use_container_width=True)

    # 3. محاكي القرار التجاري (What-If Promotion & Pricing Simulator)
    st.markdown('<div class="section-header">Executive Decision Simulator: Promotion Margin Calculator</div>', unsafe_allow_html=True)
    sim_col1, sim_col2, sim_col3 = st.columns([1.0, 1.0, 1.5])

    avg_regular_units = filtered_sales[~filtered_sales["is_promotion"]]["units_sold"].mean()

    with sim_col1:
        sim_discount = st.slider("Proposed Discount Rate (%)", min_value=0, max_value=40, value=20, step=5)
    with sim_col2:
        sim_lift = st.slider("Expected Demand Lift (%)", min_value=0, max_value=120, value=55, step=5)

    sim_price = base_price * (1.0 - sim_discount / 100.0)
    sim_units = avg_regular_units * (1.0 + sim_lift / 100.0)
    sim_daily_profit = sim_units * (sim_price - unit_cost)
    sim_profit_delta = sim_daily_profit - prof_no_promo

    with sim_col3:
        status_text = "PROFITABLE STRATEGY" if sim_profit_delta >= 0 else "MARGIN EROSION WARNING (LOSS)"
        st.metric(
            label=f"Simulated Daily Net Profit ({status_text})",
            value=f"${sim_daily_profit:,.2f} / day",
            delta=f"{sim_profit_delta:+.2f} USD/day vs Regular Price (${base_price:.2f})",
        )

    # 4. جدول التوقعات اليومية النظيف (مخفي داخل قائمة قابلة للفتح لمن يريد التفاصيل الرقمية)
    with st.expander("View Detailed 60-Day Forecast vs. Actuals Table (Nov - Dec 2025)"):
        clean_fc = filtered_forecast.copy()
        clean_fc["sale_date"] = clean_fc["sale_date"].dt.strftime("%Y-%m-%d")
        clean_fc["error_units"] = clean_fc["predicted_units"] - clean_fc["units_sold"]
        st.dataframe(clean_fc, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()