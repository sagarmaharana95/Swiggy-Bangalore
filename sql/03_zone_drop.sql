-- Q3: Zone-wise change in delivered orders (avg weekly: wk 1-6 vs wk 7-8)
WITH z AS (
  SELECT zone,
         1.0 * SUM(CASE WHEN week <= 6 THEN 1 END) / 6 AS base_wk,
         1.0 * SUM(CASE WHEN week >= 7 THEN 1 END) / 2 AS drop_wk
  FROM orders WHERE status = 'delivered'
  GROUP BY zone
)
SELECT zone, ROUND(base_wk) AS base_wk, ROUND(drop_wk) AS drop_wk,
       ROUND(100.0 * (drop_wk - base_wk) / base_wk, 1) AS pct_change
FROM z ORDER BY pct_change;
