-- Q1: Weekly delivered orders and week-over-week % change
WITH w AS (
  SELECT week, COUNT(*) AS orders
  FROM orders WHERE status = 'delivered'
  GROUP BY week
)
SELECT week, orders,
       ROUND(100.0 * (orders - LAG(orders) OVER (ORDER BY week))
             / LAG(orders) OVER (ORDER BY week), 1) AS wow_pct
FROM w;
