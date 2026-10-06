SELECT CASE WHEN order_date IN ('2026-09-17', '2026-09-18') THEN '3_rain_days'
            WHEN week <= 6 THEN '1_normal_wk1_6'
            ELSE '2_wk7_8_no_rain' END AS day_type,
       COUNT(*) AS orders,
       ROUND(AVG(delivery_mins), 1) AS avg_delivery_mins,
       ROUND(100.0 * SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*), 1) AS cancel_pct
FROM orders
GROUP BY day_type
ORDER BY day_type;