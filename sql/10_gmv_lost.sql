WITH z AS (
  SELECT zone,
         1.0 * SUM(CASE WHEN week <= 6 THEN 1 END) / 6 AS base_wk,
         1.0 * SUM(CASE WHEN week >= 7 THEN 1 END) / 2 AS drop_wk,
         AVG(order_value) AS aov
  FROM orders
  WHERE status = 'delivered'
  GROUP BY zone
)
SELECT zone,
       ROUND(base_wk - drop_wk)               AS orders_lost_per_week,
       ROUND(aov)                             AS avg_order_value,
       ROUND((base_wk - drop_wk) * aov)       AS gmv_lost_per_week
FROM z
ORDER BY gmv_lost_per_week DESC;