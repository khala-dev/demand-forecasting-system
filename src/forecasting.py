import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from src.database import get_db_engine


def load_sales_data(engine):
    query = """
    SELECT 
        sale_date,
        store_id,
        store_name,
        product_id,
        product_name,
        units_sold,
        selling_price,
        is_promotion,
        temperature_c
    FROM seles_analytics_view
    ORDER BY store_id, product_id, sale_date;
    """
    df = pd.read_sql(query, engine)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    return df


def create_time_features(df):
    df = df.copy()

    # تحويل التاريخ إلى أرقام (رقم اليوم في الأسبوع، الشهر، وهل هو ويكاند)
    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month
    df["day_of_year"] = df["sale_date"].dt.dayofyear
    df["is_weekend"] = df["day_of_week"].isin([4, 5]).astype(int)
    df["is_promotion"] = df["is_promotion"].astype(int)

    # إزاحة المبيعات بسطر (lag_1) وبـ 7 أسطر (lag_7) لكل منتج في كل متجر وحده
    grp = df.groupby(["store_id", "product_id"])["units_sold"]
    df["lag_1"] = grp.shift(1)
    df["lag_7"] = grp.shift(7)
    df["rolling_mean_7"] = grp.shift(1).rolling(window=7).mean()

    df = df.dropna().reset_index(drop=True)
    return df


def train_and_evaluate(df, engine):
    cutoff_date = "2025-11-01"
    train_df = df[df["sale_date"] < cutoff_date]
    test_df = df[df["sale_date"] >= cutoff_date].copy()

    feature_cols = [
        "store_id",
        "product_id",
        "selling_price",
        "is_promotion",
        "temperature_c",
        "day_of_week",
        "month",
        "day_of_year",
        "is_weekend",
        "lag_1",
        "lag_7",
        "rolling_mean_7",
    ]
    target_col = "units_sold"

    X_train, y_train = train_df[feature_cols], train_df[target_col]
    X_test, y_test = test_df[feature_cols], test_df[target_col]

    print(f"[INFO]Training model on {len(train_df)} rows (up to {cutoff_date})...")
    model = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, random_state=42)
    model.fit(X_train, y_train)

    raw_predictions = model.predict(X_test)
    test_df["predicted_units"] = np.maximum(0, np.round(raw_predictions)).astype(int)

    mae = mean_absolute_error(y_test, test_df["predicted_units"])
    r2 = r2_score(y_test, test_df["predicted_units"])

    print(f"[INFO]Evaluation on Test Period ({len(test_df)} rows - Nov & Dec 2025):")
    print(f"  [info] Mean Absolute Error (MAE): {mae:.2f} units")
    print(f"  [info] R² Score (Accuracy Fit):   {r2:.2%}\n")

    summary = (
        test_df.groupby("product_name")[["units_sold", "predicted_units"]]
        .sum()
        .reset_index()
    )
    summary["diff_units"] = summary["predicted_units"] - summary["units_sold"]
    print("===[INFO] Inventory Forecast vs Actual Demand (Nov - Dec 2025) ===")
    print(summary.to_string(index=False))

    output_cols = [
        "sale_date",
        "store_id",
        "store_name",
        "product_id",
        "product_name",
        "units_sold",
        "predicted_units",
        "selling_price",
        "is_promotion",
    ]
    test_df[output_cols].to_sql("demand_forecasts", engine, if_exists="replace", index=False)
    print("\n Saved predictions to PostgreSQL table: 'demand_forecasts'!")


if __name__ == "__main__":
    db_engine = get_db_engine()
    raw_df = load_sales_data(db_engine)
    featured_df = create_time_features(raw_df)
    train_and_evaluate(featured_df, db_engine)