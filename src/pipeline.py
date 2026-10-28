import numpy as np
import pandas as pd
from sqlalchemy import text
from src.database import get_db_engine

def seed_dimensions(engine):
    with engine.connect() as conn:
        store_count = conn.execute(text("SELECT COUNT(*) FROM stores;")).scalar()
        if store_count > 0:
            print("Dimension tables already contain data. Skipping seeding.")
            return

    stores_data = [
        {"store_name": "Algiers Center Mall", "city": "Algiers", "store_type": "Flagship"},
        {"store_name": "Oran Marina Hub", "city": "Oran", "store_type": "Standard"},
        {"store_name": "Constantine Express", "city": "Constantine", "store_type": "Express"},
    ]
    df_stores = pd.DataFrame(stores_data)

    products_data = [
        {"product_name": "Wireless Noise-Canceling Headphones", "category": "Electronics", "unit_cost": 45.00, "base_price": 89.99},
        {"product_name": "Ergonomic Mechanical Keyboard", "category": "Electronics", "unit_cost": 35.00, "base_price": 69.99},
        {"product_name": "Smart Fitness Watch", "category": "Wearables", "unit_cost": 28.00, "base_price": 59.99},
        {"product_name": "Portable Power Bank 20000mAh", "category": "Accessories", "unit_cost": 12.50, "base_price": 29.99},
        {"product_name": "USB-C Fast Charger 65W", "category": "Accessories", "unit_cost": 8.00, "base_price": 19.99},
    ]
    df_products = pd.DataFrame(products_data)

    df_stores.to_sql("stores", engine, if_exists="append", index=False)
    df_products.to_sql("products", engine, if_exists="append", index=False)
    print(f"Successfully inserted {len(df_stores)} stores and {len(df_products)} products!")


def generate_and_seed_sales(engine):
    # 1. حماية ضد التكرار: التحقق مما إذا كان جدول المبيعات معمراً من قبل
    with engine.connect() as conn:
        sales_count = conn.execute(text("SELECT COUNT(*) FROM daily_sales;")).scalar()
        if sales_count > 0:
            print(f"ℹdaily_sales already contains {sales_count} rows. Skipping generation.")
            return

    print("Generating 2 years of realistic daily sales data...")
    np.random.seed(42)  # لتثبيت العشوائية والحصول على نفس النتائج دائماً

    # 2. قراءة المتاجر والمنتجات مع الـ IDs الخاصة بها من PostgreSQL
    df_stores = pd.read_sql("SELECT store_id, store_type FROM stores;", engine)
    df_products = pd.read_sql("SELECT product_id, category, base_price FROM products;", engine)

    # 3. إنشاء محور الزمن (سنتين: 2024 و 2025)
    dates = pd.date_range(start="2024-01-01", end="2025-12-31", freq="D")

    store_multipliers = {"Flagship": 1.8, "Standard": 1.0, "Express": 0.6}
    records = []

    for current_date in dates:
        day_of_year = current_date.dayofyear
        is_weekend = current_date.weekday() in [4, 5]  # الجمعة والسبت

        # حساب درجة الحرارة الموسمية (تكون دافئة في الصيف وباردة في الشتاء)
        seasonal_wave = np.sin(2 * np.pi * (day_of_year - 105) / 365.25)
        base_temp = 22.0 + 10.0 * seasonal_wave

        for _, store in df_stores.iterrows():
            store_factor = store_multipliers[store["store_type"]]
            daily_temp = round(base_temp + np.random.normal(0, 2.0), 1)

            for _, prod in df_products.iterrows():
                base_price = float(prod["base_price"])
                # المنتجات الرخيصة تباع بكميات يومية أكبر طبيعياً من المنتجات الغالية
                base_demand = 25.0 if base_price < 40 else 12.0

                # احتمال 15% وجود عرض ترويجي (تخفيض 20% في السعر)
                is_promo = bool(np.random.rand() < 0.15)
                selling_price = round(base_price * 0.80, 2) if is_promo else base_price

                # تجميع العوامل المؤثرة على الطلب
                weekend_factor = 1.30 if is_weekend else 1.0
                promo_factor = 1.55 if is_promo else 1.0
                season_factor = 1.0 + 0.15 * seasonal_wave

                expected_units = base_demand * store_factor * weekend_factor * promo_factor * season_factor
                units_sold = int(np.random.poisson(lam=max(1.0, expected_units)))

                records.append({
                    "sale_date": current_date.date(),
                    "store_id": int(store["store_id"]),
                    "product_id": int(prod["product_id"]),
                    "units_sold": units_sold,
                    "selling_price": selling_price,
                    "is_promotion": is_promo,
                    "temperature_c": daily_temp,
                })

    # 4. تحويل القائمة إلى DataFrame وضخها في PostgreSQL على دفعات
    df_sales = pd.DataFrame(records)
    df_sales.to_sql("daily_sales", engine, if_exists="append", index=False, chunksize=1000)
    print(f"Successfully generated and inserted {len(df_sales)} daily sales records!")


if __name__ == "__main__":
    db_engine = get_db_engine()
    seed_dimensions(db_engine)
    generate_and_seed_sales(db_engine)