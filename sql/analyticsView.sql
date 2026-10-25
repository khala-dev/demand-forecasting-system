CREATE OR REPLACE VIEW seles_analytics_view AS
SELECT
s.sale_id,
    s.sale_date,
    st.store_id,
    st.store_name,
    st.city,
    st.store_type,
    p.product_id,
    p.product_name,
    p.category,
    s.units_sold,
    p.unit_cost,
    p.base_price,
    s.selling_price,
    s.is_promotion,
    s.temperature_c,
    --الحسابات المالية
    ROUND(s.units_sold * s.selling_price, 2) AS revenue,
    ROUND(s.units_sold * p.unit_cost, 2) AS total_cost,
    ROUND(s.units_sold * (s.selling_price - p.unit_cost), 2) AS net_profit
FROM daily_sales s
JOIN stores st ON s.store_id = st.store_id
JOIN products p ON s.product_id = p.product_id;