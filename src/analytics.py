import pandas as pd
from src.database import get_db_engine

def run_financial_diagnostics(engine):
    print("Fetching data from sales_analytics_view...\n")
    
    # 1. الاستعلام الأول: تقييم المتاجر وحساب هامش الربح المئوي
    store_query = """
    SELECT 
        store_name,
        city,
        store_type,
        SUM(units_sold) AS total_units,
        ROUND(SUM(revenue), 2) AS total_revenue,
        ROUND(SUM(net_profit), 2) AS total_profit,
        ROUND((SUM(net_profit) / SUM(revenue)) * 100, 1) AS profit_margin_pct
    FROM seles_analytics_view
    GROUP BY store_name, city, store_type
    ORDER BY total_profit DESC;
    """
    df_stores = pd.read_sql(store_query, engine)
    print("=== 1. Store Performance Ranking ===")
    print(df_stores.to_string(index=False))
    print("\n" + "-"*65 + "\n")

    # 2. الاستعلام الثاني: مقارنة ربح كل منتج (بدون تخفيض vs مع تخفيض) جنب لجنب
    promo_product_query = """
    SELECT 
        product_name,
        ROUND(AVG(CASE WHEN is_promotion = FALSE THEN net_profit END), 2) AS profit_no_promo,
        ROUND(AVG(CASE WHEN is_promotion = TRUE THEN net_profit END), 2) AS profit_with_promo,
        ROUND(
            AVG(CASE WHEN is_promotion = TRUE THEN net_profit END) - 
            AVG(CASE WHEN is_promotion = FALSE THEN net_profit END), 2
        ) AS profit_difference
    FROM seles_analytics_view
    GROUP BY product_name
    ORDER BY profit_difference DESC;
    """
    df_promo = pd.read_sql(promo_product_query, engine)
    print("=== 2. Promotion Impact by Product (Daily Avg Profit) ===")
    print(df_promo.to_string(index=False))
    print("\n" + "-"*65 + "\n")

if __name__ == "__main__":
    db_engine = get_db_engine()
    run_financial_diagnostics(db_engine)